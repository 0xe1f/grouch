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

from .celery_app import _config
from .celery_app import celery_app
from .celery_app import get_dao
from .celery_app import per_user
from .feeds import import_feeds
from .feeds import import_feed_results
from common import first_or_none
from common.url_safety import check_url_remote
from common.url_safety import is_safe_url
from dao import BulkUpdateQueue
from dao import Database
from entity import Article
from entity import Folder
from entity import Subscription
from datetime import datetime
from itertools import batched
from parser import ParseResult
from port import PortDoc
from port import Source
from port.objects import Group
from time import time
import logging
import parser


def sync_subs(
    dao: Database,
    bulk_q: BulkUpdateQueue,
    user_id: str,
    feed_ids: set[str]|None=None,
):
    # Ensure nothing's left to write
    bulk_q.flush()

    for sub_id, feed_id, folder_id, synced in dao.subs.iter_metadata_by_user_by_synced(user_id):
        if feed_ids and feed_id not in feed_ids:
            continue

        max_synced = None
        read_batch_size = 40

        entry_iter = (
            dao.entries.iter_latest(feed_id, _FIRST_SYNC_MAX_ENTRIES)
            if synced is None
            else dao.entries.iter_updated_since(feed_id, synced)
        )

        # Fetch entries that have updated
        marked_unread = 0
        updated_article_count = 0
        for entry_batch in batched(entry_iter, read_batch_size):
            entry_map = {}
            for entry in entry_batch:
                entry_map[entry.id] = entry
                if entry.updated:
                    max_synced = entry.updated if max_synced is None else max(max_synced, entry.updated)

            # Batch existing articles
            for article in dao.articles.iter_by_user_by_entry(user_id, *entry_map.keys()):
                entry = entry_map.pop(article.entry_id)
                if article.synced == entry.updated:
                    # Nothing's changed
                    continue
                marked_unread += 1
                updated_article_count += 1
                article.toggle_prop(Article.PROP_UNREAD, True)
                article.synced = entry.updated
                article.published = entry.published
                bulk_q.enqueue(article)

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
                bulk_q.enqueue(article)

        # Update sub, if there were changes
        if updated_article_count and max_synced is not None:
            sub = first_or_none(dao.subs.find_by_id(sub_id))
            sub.last_synced = max_synced
            bulk_q.enqueue(sub)


_MAX_FEED_CHOICES = 8
_FIRST_SYNC_MAX_ENTRIES = 100


def subscribe_user_unknown_url(
    dao: Database,
    user_id: str,
    url: str,
    folder_id: str|None = None,
) -> dict|None:
    """Subscribe the user to the given URL.

    Returns a dict with event data if the client needs to select from multiple
    feeds, or None if the subscription was handled (or failed).
    """
    with dao.new_q() as bulk_q:
        if not _subscribe_local_feeds(dao, bulk_q, user_id, Source(feed_url=url)):
            # Subscribed to available feed
            return None

        # Parse contents of URL
        if not (result := parser.parse_url(url)):
            logging.error(f"No valid feeds available for '{url}'")
            return None

        if result.feed:
            # URL successfully parsed as feed
            _subscribe_user_parsed(dao, bulk_q, user_id, result)
        elif alts := result.alternatives:
            if len(alts) == 1:
                # Only one option — subscribe without bothering the user
                _subscribe_user(dao, bulk_q, user_id, Source(feed_url=alts[0].url))
            else:
                # Multiple feeds found — ask the client to pick one
                logging.debug(f"Multiple feeds for '{url}', requesting selection")
                return {
                    "pageUrl": url,
                    "feeds": [{"url": a.url, "title": a.title} for a in alts[:_MAX_FEED_CHOICES]],
                    "folderId": folder_id,
                }

    logging.debug(f"{bulk_q.written_count}/{bulk_q.enqueued_count} objects written")
    return None


def import_user_subs(
    dao: Database,
    user_id: str,
    doc: PortDoc,
):
    existing_folders = dao.folders.find_by_user(user_id)
    folder_name_map = { folder.title:folder.id for folder in existing_folders }
    folder_group_id_map = {}

    with dao.new_q() as bulk_q:
        for group in doc.groups:
            if group.title not in folder_name_map:
                folder = Folder()
                folder.title = group.title
                folder.user_id = user_id
                bulk_q.enqueue(folder)
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

        _subscribe_user(dao, bulk_q, user_id, *sources)

    logging.debug(f"{bulk_q.written_count}/{bulk_q.enqueued_count} objects written; {bulk_q.commit_count} commits")


def unsubscribe(
    dao: Database,
    *sub_ids: str,
):
    start_time = time()

    with dao.new_q() as bulk_q:
        remove_subscriptions(dao, bulk_q, *sub_ids)

    logging.info(f"Unsub {len(sub_ids)} subs: {bulk_q.written_count}/{bulk_q.enqueued_count} objects written ({time() - start_time:.2}s)")


def _subscribe_user(
    dao: Database,
    bulk_q: BulkUpdateQueue,
    user_id: str,
    *sub_sources: Source,
):
    # Subscribe to all available feeds, get list of remaining
    remaining_sources = _subscribe_local_feeds(dao, bulk_q, user_id, *sub_sources)

    # Remainder needs to be fetched
    new_feed_urls = [source.feed_url for source in remaining_sources]

    if len(new_feed_urls) > 0:
        # Import new feeds
        imported = import_feeds(bulk_q, *new_feed_urls)
        remaining_sources.difference_update(imported)

        # Attempt resubscribing again
        if remaining_sources:
            _subscribe_local_feeds(dao, bulk_q, user_id, *remaining_sources)


def _subscribe_user_parsed(
    dao: Database,
    bulk_q: BulkUpdateQueue,
    user_id: str,
    *results: ParseResult,
):
    successful = [result for result in results if result.feed]
    import_feed_results(bulk_q, *successful)
    _subscribe_local_feeds(dao, bulk_q, user_id, *[Source(feed_url=result.url) for result in successful])


# Returns subs that could not be subscribed to (no matching feed)
def _subscribe_local_feeds(
    dao: Database,
    bulk_q: BulkUpdateQueue,
    user_id: str,
    *sources: Source,
) -> set[Source]:
    # Ensure nothing pending write
    bulk_q.flush()

    source_dict = { source.feed_url:source for source in sources }
    remaining_sources = set(source_dict.values())
    subbed_feed_ids = set()

    if not (existing_feeds_by_url := dao.feeds.map_metadata_by_url(*source_dict.keys())):
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

        bulk_q.enqueue(sub)
        subbed_feed_ids.add(feed_id)
        remaining_sources.remove(sub_source)

    sync_subs(dao, bulk_q, user_id, subbed_feed_ids)

    return remaining_sources


def remove_subscriptions(
    dao: Database,
    bulk_q: BulkUpdateQueue,
    *sub_ids: str,
) -> bool:
    pending_count = bulk_q.pending_count
    written_count = bulk_q.written_count
    enqueued_count = bulk_q.enqueued_count

    for sub_id in sub_ids:
        pending_count = bulk_q.pending_count
        written_count = bulk_q.written_count
        enqueued_count = bulk_q.enqueued_count

        dao.articles.delete_by_sub(bulk_q, sub_id)
        bulk_q.flush()

        written_count = bulk_q.written_count - written_count - pending_count
        enqueued_count = bulk_q.enqueued_count - enqueued_count

        if written_count == enqueued_count:
            sub = first_or_none(dao.subs.find_by_id(sub_id))
            sub.mark_deleted()
            bulk_q.enqueue(sub)

    bulk_q.flush()

    written_count = bulk_q.written_count - written_count - pending_count
    enqueued_count = bulk_q.enqueued_count - enqueued_count

    # If all_articles_removed, but enqueued_count != written_count,
    # then at least one subscription failed to write
    return enqueued_count == written_count


# ---------------------------------------------------------------------------
# Celery task entry points
# ---------------------------------------------------------------------------

@celery_app.task(bind=True, max_retries=30, default_retry_delay=10)
@per_user
def subs_sync(self, user_id: str, notify: bool = False):
    dao = get_dao()
    with dao.new_q() as bulk_q:
        sync_subs(dao, bulk_q, user_id)

    logging.debug(f"{bulk_q.written_count}/{bulk_q.enqueued_count} records written; {bulk_q.commit_count} commits")

    if notify:
        from tasks.worker_notify import notify as send_notification
        send_notification(user_id, "refresh")


@celery_app.task(bind=True, max_retries=30, default_retry_delay=10)
@per_user
def subs_subscribe_url(self, user_id: str, url: str, folder_id: str|None = None, notify: bool = False):
    selection = subscribe_user_unknown_url(get_dao(), user_id, url, folder_id)

    if notify:
        from tasks.worker_notify import notify as send_notification
        if selection is not None:
            send_notification(user_id, "select_feed", selection)
        else:
            send_notification(user_id, "refresh")


@celery_app.task(bind=True, max_retries=30, default_retry_delay=10)
@per_user
def subs_import(self, user_id: str, doc_dict: dict, notify: bool = False):
    doc = PortDoc.from_dict(doc_dict)
    filtered_doc = PortDoc()
    for group in doc.groups:
        filtered_doc.append_group(group)

    rejected_count = 0
    for source in doc.sources:
        if not is_safe_url(source.feed_url):
            logging.warning(f"Rejected unsafe OPML URL: {source.feed_url}")
            rejected_count += 1
        elif not check_url_remote(source.feed_url, _config):
            rejected_count += 1
        else:
            filtered_doc.append_source(source)

    import_user_subs(get_dao(), user_id, filtered_doc)

    if notify:
        from tasks.worker_notify import notify as send_notification
        if rejected_count > 0:
            send_notification(user_id, "warning", f"{rejected_count} feed(s) were rejected during import due to a security check and were not added.")
        send_notification(user_id, "refresh")


@celery_app.task(bind=True, max_retries=30, default_retry_delay=10)
@per_user
def subs_unsubscribe(self, user_id: str, sub_ids: list[str]):
    unsubscribe(get_dao(), *sub_ids)
