from common import now_in_iso
from datatype import EntryContent
from store.bulk_update_queue import BulkUpdateQueue
from store.connection import Connection

def find_entries_by_id(conn: Connection, *entry_ids: str) -> list[EntryContent]:
    matches = []
    for item in conn.db.view("_all_docs", keys=entry_ids, include_docs=True):
        doc = item.get("doc")
        if doc:
            matches.append(EntryContent(doc))

    return matches

def find_entries_fetched_since(conn: Connection, feed_id: str, updated_min: str):
    for item in conn.db.view("maint/entries-by-feed-updated", start_key=[ feed_id, updated_min ], end_key=[ feed_id, {}], include_docs=True):
        yield EntryContent(item["doc"])

def find_entries_by_uid(conn: Connection, feed_id: str, *entry_uids: str):
    options = {
        "include_docs": True,
        "keys": [[feed_id, entry_uid] for entry_uid in entry_uids],
    }
    results = conn.db.view("maint/entries-by-feed-id", **options)
    for item in results:
        yield EntryContent(item["doc"])

def enqueue_entries(bulk_queue: BulkUpdateQueue, *entries: EntryContent):
    for entry in entries:
        if not entry.id:
            entry.id = entry.build_key()
        entry.digest = entry.computed_digest()
        entry.updated = now_in_iso()

        bulk_queue.enqueue_tuple((entry.doc(), entry))
