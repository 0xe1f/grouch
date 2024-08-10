from common import first_or_none
from common import now_in_iso
from datatype import Article
from datatype import Subscription
from itertools import batched
from store import find_subs_by_id
from store import find_articles_by_entry
from store import find_entries_fetched_since
from store import find_feed_ids_by_url
from store import find_user_subs_synced
from store import BulkUpdateQueue
from store import Connection
from subscribe import SubSource
from tasks import import_feeds
import logging

def sync_subs(conn: Connection, user_id: str):
    # TODO: mayhap split this across multiple executors
    with BulkUpdateQueue(conn) as bulk_q:
        # FIXME: migrate to iterview
        for sub_id, feed_id, folder_id, synced in find_user_subs_synced(conn, user_id):
            max_synced = ""
            read_batch_size = 40

            # Fetch entries that have updated
            marked_unread = 0
            updated_article_count = 0
            for entry_batch in batched(find_entries_fetched_since(conn, feed_id, synced), read_batch_size):
                entry_map = {}
                for entry in entry_batch:
                    entry_map[entry.id] = entry
                    max_synced = max(max_synced, entry.updated or "")

                # Batch existing articles
                for article in find_articles_by_entry(conn, user_id, *entry_map.keys()):
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
                sub = first_or_none(find_subs_by_id(conn, sub_id))
                sub.last_synced = max_synced
                sub.unread_count += marked_unread
                bulk_q.enqueue_flex(sub)

    logging.debug(f"{bulk_q.written_count}/{bulk_q.enqueued_count} records written")

def subscribe_user(conn: Connection, user_id: str, *sub_sources: SubSource):
    # Subscribe to all available feeds, get list of remaining
    remaining_sources = _subscribe_current_feeds(conn, user_id, *sub_sources)

    # Remainder needs to be fetched
    new_feed_urls = [source.url for source in remaining_sources]

    # Create folders
    # FIXME!! skip folders for now
    # folder_title_map = create_folders(user_id, *[sub_folder.title for sub_folder in sub_folders])
    # print(folder_title_map)
    # return

    if len(new_feed_urls) > 0:
        # Import new feeds
        imported = import_feeds(conn, *new_feed_urls)
        remaining_sources.difference_update(imported)

        # Attempt resubscribing again
        # FIXME - reconsider this when this becomes a task queue
        if remaining_sources:
            _subscribe_current_feeds(conn, user_id, *remaining_sources)

def move_sub(conn: Connection, sub_id: str, dest_folder_id: str|None):
    logging.info(f"Moving {sub_id} to {dest_folder_id}")
    for x in range(5):
        logging.info("sleeping")
    logging.info("ALL DONE")

# Returns subs that could not be subscribed to (no matching feed)
def _subscribe_current_feeds(conn: Connection, user_id: str, *sub_sources: SubSource) -> set[SubSource]:
    source_dict = { source.url:source for source in sub_sources }
    all_subs = set(source_dict.values())
    existing_feeds_by_url = find_feed_ids_by_url(conn, *source_dict.keys())
    if not existing_feeds_by_url:
        return all_subs

    with BulkUpdateQueue(conn) as bulk_q:
        for url, feed_id in existing_feeds_by_url.items():
            sub_source = source_dict[url]
            sub = Subscription()
            sub.user_id = user_id
            sub.feed_id = feed_id
            # FIXME!!
            # if sub_source.parent_id:
            #     sub.folder_id = folder_id_map[sub_source.parent_id]
            sub.title = sub_source.title
            sub.subscribed = now_in_iso()

            bulk_q.enqueue_flex(sub)
            all_subs.remove(sub_source)

    logging.info(f"Subscribed to {bulk_q.written_count} feeds")

    return all_subs
