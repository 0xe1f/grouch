# Copyright (C) 2024 Akop Karapetyan
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from common import first_or_none
from datatype import Article
from datatype import Folder
from datatype import Subscription
from datetime import datetime
from itertools import batched
from parser import ParseResult
from port import PortDoc
from port import Source
from store import find_folders_by_user
from store import find_subs_by_id
from store import find_articles_by_entry
from store import find_entries_fetched_since
from store import find_feed_meta_by_url
from store import find_user_subs_synced
from store import generate_subscriptions_by_folder
from store import generate_subscriptions_by_user
from store import BulkUpdateQueue
from store import Connection
from tasks.feeds import import_feeds
from tasks.feeds import import_feed_results
from tasks.articles import remove_articles_by_sub
from tasks.articles import mark_articles_as_read_by_folder
from tasks.articles import mark_articles_as_read_by_sub
from tasks.articles import mark_articles_as_read_by_user
from time import time
import logging
import parser

def sync_subs(bulk_q: BulkUpdateQueue, user_id: str, feed_ids: set[str]|None=None):
    # Ensure nothing's left to write
    bulk_q.flush()

    # FIXME: migrate to iterview
    for sub_id, feed_id, folder_id, synced in find_user_subs_synced(bulk_q.connection, user_id):
        if feed_ids and feed_id not in feed_ids:
            continue

        max_synced = 0
        read_batch_size = 40

        # Fetch entries that have updated
        marked_unread = 0
        updated_article_count = 0
        for entry_batch in batched(find_entries_fetched_since(bulk_q.connection, feed_id, synced), read_batch_size):
            entry_map = {}
            for entry in entry_batch:
                entry_map[entry.id] = entry
                max_synced = max(max_synced, entry.updated or "")

            # Batch existing articles
            for article in find_articles_by_entry(bulk_q.connection, user_id, *entry_map.keys()):
                entry = entry_map.pop(article.entry_id)
                if article.synced == entry.updated:
                    # Nothing's changed
                    continue
                marked_unread += 1
                updated_article_count += 1
                article.toggle_prop(Article.PROP_UNREAD, True)
                article.synced = entry.updated
                article.published = entry.published
                bulk_q.enqueue_flex(article)

            # Batch new articles
            for entry in entry_map.values():
                marked_unread += 1
                updated_article_count += 1
                article = Article()
                article.user_id = user_id
                article.subscription_id = sub_id
                article.folder_id = folder_id
                article.entry_id = entry.id
                article.toggle_prop(Article.PROP_UNREAD, True)
                article.synced = entry.updated
                article.published = entry.published
                bulk_q.enqueue_flex(article)

        # Update sub, if there were changes
        if updated_article_count:
            sub = first_or_none(find_subs_by_id(bulk_q.connection, sub_id))
            sub.last_synced = max_synced
            sub.unread_count += marked_unread
            bulk_q.enqueue_flex(sub)

def subscribe_user_unknown_url(conn: Connection, user_id: str, url: str):
    with BulkUpdateQueue(conn, track_ids=False) as bulk_q:
        # TODO: account for possibility of multiple feeds per URL
        if not _subscribe_local_feeds(bulk_q, user_id, Source(feed_url=url)):
            # Subscribed to available feed
            return

        # Parse contents of URL
        if not (result := parser.parse_url(url)):
            logging.error(f"No valid feeds available for '{url}'")
            return

        if result.feed:
            # URL successfully parsed as feed
            _subscribe_user_parsed(bulk_q, user_id, result)
        elif alts := result.alternatives:
            # Not a feed, but alternatives are available. Use first available
            # TODO: allow selection from multiple feeds
            _subscribe_user(bulk_q, user_id, Source(feed_url=alts[0]))

    logging.debug(f"{bulk_q.written_count}/{bulk_q.enqueued_count} objects written")

def import_user_subs(conn: Connection, user_id: str, doc: PortDoc):
    existing_folders = find_folders_by_user(conn, user_id)
    folder_name_map = { folder.title:folder.id for folder in existing_folders }
    folder_group_id_map = {}

    with BulkUpdateQueue(conn, track_ids=False) as bulk_q:
        for group in doc.groups:
            if group.title not in folder_name_map:
                folder = Folder()
                folder.title = group.title
                folder.user_id = user_id
                bulk_q.enqueue_flex(folder)
                folder_group_id_map[group.id] = folder.new_key()
            else:
                folder_group_id_map[group.id] = folder_name_map[group.title]

        # Need to update parent_id
        sources = []
        for doc_source in doc.sources:
            sources.append(
                Source(
                    title=doc_source.title,
                    feed_url=doc_source.feed_url,
                    parent_id=folder_group_id_map.get(doc_source.parent_id)
                )
            )

        _subscribe_user(bulk_q, user_id, *sources)

    logging.debug(f"{bulk_q.written_count}/{bulk_q.enqueued_count} objects written; {bulk_q.commit_count} commits")

def unsubscribe(conn: Connection, *sub_ids: int):
    start_time = time()

    with BulkUpdateQueue(conn, track_ids=False) as bulk_q:
        remove_subscriptions(bulk_q, *sub_ids)

    logging.info(f"Unsub {len(sub_ids)} subs: {bulk_q.written_count}/{bulk_q.enqueued_count} objects written ({time() - start_time:.2}s)")

def mark_subs_read_by_user(conn: Connection, user_id: str):
    start_time = time()
    logging.debug(f"Marking {user_id}'s subs as read")

    with BulkUpdateQueue(conn, track_ids=False) as bulk_q:
        mark_articles_as_read_by_user(bulk_q, user_id)
        for sub in generate_subscriptions_by_user(bulk_q.connection, user_id):
            sub.unread_count = 0
            bulk_q.enqueue_flex(sub)

    logging.info(f"Wrote {bulk_q.written_count}/{bulk_q.enqueued_count} objects ({time() - start_time:.2}s)")

def mark_subs_read_by_folder(conn: Connection, folder_id: str):
    start_time = time()
    logging.debug(f"Marking {folder_id} as read")

    with BulkUpdateQueue(conn, track_ids=False) as bulk_q:
        mark_articles_as_read_by_folder(bulk_q, folder_id)
        for sub in generate_subscriptions_by_folder(bulk_q.connection, folder_id):
            sub.unread_count = 0
            bulk_q.enqueue_flex(sub)

    logging.info(f"Wrote {bulk_q.written_count}/{bulk_q.enqueued_count} objects ({time() - start_time:.2}s)")

def mark_sub_read(conn: Connection, sub_id: str):
    start_time = time()
    logging.debug(f"Marking {sub_id} as read")

    with BulkUpdateQueue(conn, track_ids=False) as bulk_q:
        changed = mark_articles_as_read_by_sub(bulk_q, sub_id)
        if sub := first_or_none(find_subs_by_id(bulk_q.connection, sub_id)):
            sub.unread_count -= changed
            bulk_q.enqueue_flex(sub)

    logging.info(f"Wrote {bulk_q.written_count}/{bulk_q.enqueued_count} objects ({time() - start_time:.2}s)")

# ---

def _subscribe_user(bulk_q: BulkUpdateQueue, user_id: str, *sub_sources: Source):
    # Subscribe to all available feeds, get list of remaining
    remaining_sources = _subscribe_local_feeds(bulk_q, user_id, *sub_sources)

    # Remainder needs to be fetched
    new_feed_urls = [source.feed_url for source in remaining_sources]

    if len(new_feed_urls) > 0:
        # Import new feeds
        imported = import_feeds(bulk_q, *new_feed_urls)
        remaining_sources.difference_update(imported)

        # Attempt resubscribing again
        if remaining_sources:
            _subscribe_local_feeds(bulk_q, user_id, *remaining_sources)

def _subscribe_user_parsed(bulk_q: BulkUpdateQueue, user_id: str, *results: ParseResult):
    successful = [result for result in results if result.feed]
    import_feed_results(bulk_q, *successful)
    _subscribe_local_feeds(bulk_q, user_id, *[Source(feed_url=result.url) for result in successful])

# Returns subs that could not be subscribed to (no matching feed)
def _subscribe_local_feeds(bulk_q: BulkUpdateQueue, user_id: str, *sources: Source) -> set[Source]:
    # Ensure nothing pending write
    bulk_q.flush()

    source_dict = { source.feed_url:source for source in sources }
    remaining_sources = set(source_dict.values())
    subbed_feed_ids = set()

    if not (existing_feeds_by_url := find_feed_meta_by_url(bulk_q.connection, *source_dict.keys())):
        return remaining_sources

    for url, (feed_id, title) in existing_feeds_by_url.items():
        sub_source = source_dict[url]
        sub = Subscription()
        sub.user_id = user_id
        sub.feed_id = feed_id
        if sub_source.parent_id:
            sub.folder_id = sub_source.parent_id
        sub.title = sub_source.title or title
        sub.subscribed = datetime.now().timestamp()

        bulk_q.enqueue_flex(sub)
        subbed_feed_ids.add(feed_id)
        remaining_sources.remove(sub_source)

    sync_subs(bulk_q, user_id, subbed_feed_ids)

    return remaining_sources

def remove_subscriptions(bulk_q: BulkUpdateQueue, *sub_ids: int) -> bool:
    pending_count = bulk_q.pending_count
    written_count = bulk_q.written_count
    enqueued_count = bulk_q.enqueued_count

    for sub_id in sub_ids:
        if remove_articles_by_sub(bulk_q, sub_id):
            sub = first_or_none(find_subs_by_id(bulk_q.connection, sub_id))
            sub.mark_deleted()
            bulk_q.enqueue_flex(sub)

    bulk_q.flush()
    written_count = bulk_q.written_count - written_count - pending_count
    enqueued_count = bulk_q.enqueued_count - enqueued_count

    # If all_articles_removed, but enqueued_count != written_count,
    # then at least one subscription failed to write
    return enqueued_count == written_count
