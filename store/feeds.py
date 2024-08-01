from common import build_key
from common import format_iso
from common import now_in_iso
from datatype import FeedContent
from store.bulk_update_queue import BulkUpdateQueue
from store.connection import Connection
from time import struct_time

def find_feeds_by_id(conn: Connection, *feed_ids: str) -> list[FeedContent]:
    matches = []
    for item in conn.db.view("_all_docs", keys=feed_ids, include_docs=True):
        matches.append(FeedContent(item.doc["content"]))

    return matches

def find_feeds_by_url(conn: Connection, *urls: str) -> dict:
    matches = {}
    for item in conn.db.view("maint/feeds-by-url", keys = urls):
        matches[item.key] = item.id

    return matches

def enqueue_feeds(bulk_queue: BulkUpdateQueue, *feeds: tuple[FeedContent, str]):
    for feed, rev in feeds:
        if not feed.id:
            feed.id = build_key("feed", feed.feed_url)
        doc = {
            "_id": feed.id,
            "doc_type": "feed",
            "content": feed.doc(),
            "digest": feed.digest(),
            "updated": now_in_iso(),
        }
        if rev:
            doc["_rev"] = rev
        bulk_queue.enqueue_tuple((doc, feed))

def stale_feeds(conn: Connection, stale_start: struct_time=None):
    batch_limit = 40
    options = {
        "descending": True,
        "include_docs": True,
    }
    if stale_start:
        options.update(startkey=format_iso(stale_start))

    iterable = conn.db.iterview("maint/updated-feeds", batch_limit, **options)
    for item in iterable:
        doc = item["doc"]
        yield FeedContent(doc["content"]), doc["digest"], doc["_rev"]
