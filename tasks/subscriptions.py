from common import format_iso
from datatype import Subscription
from store import find_feeds_by_url
from store import enqueue_subs
from store import BulkUpdateQueue
from store import Connection
from subscribe import SubSource
from tasks import import_feeds
from time import gmtime
import logging

def sync_subs(conn: Connection, user_id: str):
    print(f"refresh_subs {user_id}")
    # now = time.mktime(time.localtime())
    # stale_start = time.gmtime(now - freshness_seconds)

    # bulk_q = BulkUpdateQueue(conn)
    # pending_fetch: list[tuple[FeedContent, str]] = []
    # fetch_batch_max = 40
    # # TODO: probably good to set some sort of max limit
    # for t in stale_feeds(conn, stale_start=stale_start):
    #     pending_fetch.append(t)
    #     if len(pending_fetch) >= fetch_batch_max:
    #         _freshen_stale_feed_content(conn, bulk_q, *pending_fetch)
    #         pending_fetch.clear()

    # if pending_fetch:
    #     _freshen_stale_feed_content(conn, bulk_q, *pending_fetch)
    #     pending_fetch.clear()

    # bulk_q.flush()

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
        sub.subscribed = format_iso(gmtime())

        enqueue_subs(bulk_q, (sub, None))
        all_subs.remove(sub_source)

    bulk_q.flush()

    logging.info(f"Subscribed to {bulk_q.write_ok} feeds")

    return all_subs
