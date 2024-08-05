from common import now_in_iso
from datatype import Article
from datatype import Subscription
from itertools import batched
from store import enqueue_articles
from store import enqueue_subs
from store import fetch_sub
from store import find_articles_by_entry
from store import find_entries_fetched_since
from store import find_feeds_by_url
from store import find_user_subs_synced
from store import BulkUpdateQueue
from store import Connection
from subscribe import SubSource
from tasks import import_feeds
import logging

def sync_subs(conn: Connection, user_id: str):
    bulk_q = BulkUpdateQueue(conn)

    # TODO: mayhap split this across multiple executors
    for sub_id, feed_id, synced in find_user_subs_synced(conn, user_id):
        max_synced = ""
        read_batch_size = 40

        # Fetch entries that have updated
        marked_unread = 0
        updated_article_count = 0
        for tuple_batch in batched(find_entries_fetched_since(conn, feed_id, synced), read_batch_size):
            update_map = {}
            for entry, updated in tuple_batch:
                # FIXME!!!
                update_map[entry.id] = updated or ""
                max_synced = max(max_synced, updated or "")

            # Batch existing articles
            for article, rev in find_articles_by_entry(conn, user_id, *update_map.keys()):
                updated = update_map.pop(article.entry_id)
                if article.synced == updated:
                    # Nothing's changed
                    continue
                marked_unread += 1
                updated_article_count += 1
                article.toggle_prop(Article.PROP_UNREAD, True)
                article.synced = updated
                article.published = entry.published
                enqueue_articles(bulk_q, (article, rev))

            # Batch new articles
            for entry_id, updated in update_map.items():
                marked_unread += 1
                updated_article_count += 1
                article = Article()
                article.user_id = user_id
                article.subscription_id = sub_id
                article.entry_id = entry_id
                article.toggle_prop(Article.PROP_UNREAD, True)
                article.synced = updated
                article.published = entry.published
                enqueue_articles(bulk_q, (article, None))

        # Update sub, if there were changes
        if updated_article_count:
            sub, sub_rev = fetch_sub(conn, sub_id)
            sub.last_synced = max_synced
            sub.unread_count += marked_unread
            enqueue_subs(bulk_q, (sub, sub_rev))

    bulk_q.flush()

    logging.debug(f"{bulk_q.records_written}/{bulk_q.records_enqueued} records written")

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

# Returns subs that could not be subscribed to (no matching feed)
def _subscribe_current_feeds(conn: Connection, user_id: str, *sub_sources: SubSource) -> set[SubSource]:
    source_dict = { source.url:source for source in sub_sources }
    all_subs = set(source_dict.values())
    existing_feeds_by_url = find_feeds_by_url(conn, *source_dict.keys())
    if not existing_feeds_by_url:
        return all_subs

    bulk_q = BulkUpdateQueue(conn)
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

        enqueue_subs(bulk_q, (sub, None))
        all_subs.remove(sub_source)

    bulk_q.flush()

    logging.info(f"Subscribed to {bulk_q.records_written} feeds")

    return all_subs
