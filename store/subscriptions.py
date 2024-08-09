from common import now_in_iso
from datatype import Subscription
from store import BulkUpdateQueue
from store import Connection

def find_subs_by_id(conn: Connection, *ids: str) -> list[Subscription]:
    matches = []
    for item in conn.db.view("_all_docs", keys=ids, include_docs=True):
        if "doc" in item:
            matches.append(Subscription(item["doc"]))

    return matches

def find_user_subs(conn: Connection, user_id: str) -> list[Subscription]:
    matches = []
    for item in conn.db.view("maint/sub_last_synced_by_user", start_key=[ user_id ], end_key=[ user_id, {} ], include_docs=True):
        matches.append(Subscription(item.doc))

    return matches

def find_user_subs_synced(conn: Connection, user_id: str) -> list[tuple[str, str, str]]:
    matches = []
    for doc in conn.db.view("maint/sub_last_synced_by_user", start_key=[ user_id ], end_key=[ user_id, {} ]):
        matches.append((doc.id, doc.value["feed_id"], doc.value.get("last_sync")))

    return matches

def enqueue_subs(bulk_queue: BulkUpdateQueue, *subs: Subscription):
    for sub in subs:
        if not sub.user_id:
            raise ValueError(f"Sub {sub.title} is missing user_id")
        elif not sub.feed_id:
            raise ValueError(f"Sub {sub.title} is missing feed_id")

    for sub in subs:
        if not sub.id:
            sub.id = sub.build_key()
        sub.updated = now_in_iso()
        bulk_queue.enqueue_tuple((sub.doc(), sub))
