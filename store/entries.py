from datatype import EntryContent
from store.connection import Connection
from store import views

def find_entries_by_id(conn: Connection, *entry_ids: str) -> list[EntryContent]:
    matches = []
    for item in conn.db.view(views.ALL_DOCS, keys=entry_ids, include_docs=True):
        doc = item.get("doc")
        if doc:
            matches.append(EntryContent(doc))

    return matches

def find_entries_fetched_since(conn: Connection, feed_id: str, updated_min: str):
    for item in conn.db.view("maint/entries_by_feed_updated", start_key=[ feed_id, updated_min ], end_key=[ feed_id, {}], include_docs=True):
        yield EntryContent(item["doc"])

def find_entries_by_uid(conn: Connection, feed_id: str, *entry_uids: str):
    options = {
        "include_docs": True,
        "keys": [[feed_id, entry_uid] for entry_uid in entry_uids],
    }
    results = conn.db.view(views.ENTRIES_BY_FEED, **options)
    for item in results:
        yield EntryContent(item["doc"])
