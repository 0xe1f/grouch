from common import build_key
from common import now_in_iso
from datatype import EntryContent
from store.bulk_update_queue import BulkUpdateQueue
from store.connection import Connection

def find_entries_fetched_since(conn: Connection, feed_id: str, updated_min: str):
    for doc in conn.db.view("maint/entries-by-feed-updated", start_key=[ feed_id, updated_min ], end_key=[ feed_id, {}]):
        yield (doc.id, doc.key[1])

def find_entries_by_uid(conn: Connection, feed_id: str, *entry_uids: str):
    options = {
        "include_docs": True,
        "keys": [[feed_id, entry_uid] for entry_uid in entry_uids],
    }
    results = conn.db.view("maint/entries-by-feed-id", **options)
    for item in results:
        doc = item["doc"]
        yield EntryContent(doc["content"]), doc["digest"], doc["_rev"]

def enqueue_entries(bulk_queue: BulkUpdateQueue, *entries: tuple[EntryContent, str]):
    for entry, rev in entries:
        if not entry.id:
            entry.id = build_key("entry", entry.feed_id, entry.entry_uid)
        doc = {
            "_id": entry.id,
            "doc_type": "entry",
            "content": entry.doc(),
            "digest": entry.digest(),
            "updated": now_in_iso(),
        }
        if rev:
            doc["_rev"] = rev
        bulk_queue.enqueue_tuple((doc, entry))
