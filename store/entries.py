from common import build_key
from common import now_in_iso
from couchdb.http import ResourceConflict
from datatype import EntryContent
from store import BulkUpdateQueue
from store import Connection

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
    now_iso = now_in_iso()
    for entry, rev in entries:
        if not entry.id:
            entry.id = build_key("entry", entry.feed_id, entry.entry_uid)
        doc = {
            "_id": entry.id,
            "doc_type": "entry",
            "content": entry.doc(),
            "digest": entry.digest(),
            "updated": now_iso,
        }
        if rev:
            doc["_rev"] = rev
        bulk_queue.enqueue_tuple((doc, entry))
