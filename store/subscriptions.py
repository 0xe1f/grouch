from common import now_in_iso
from common import build_key
from datatype import Subscription
from store import BulkUpdateQueue
from store import Connection

def fetch_sub(conn: Connection, sub_id: str) -> tuple[Subscription, str]:
    for item in conn.db.view("_all_docs", key=sub_id, include_docs=True):
        return Subscription(item.doc["content"]), item.doc["_rev"]

    return None

def find_user_subs(conn: Connection, user_id: str) -> list[Subscription]:
    matches = []
    for item in conn.db.view("maint/sub-last-synced-by-user", start_key=[ user_id ], end_key=[ user_id, {} ], include_docs=True):
        matches.append(Subscription(item.doc["content"]))

    return matches

def find_user_subs_synced(conn: Connection, user_id: str) -> list[tuple[str, str, str]]:
    matches = []
    for doc in conn.db.view("maint/sub-last-synced-by-user", start_key=[ user_id ], end_key=[ user_id, {} ]):
        matches.append((doc.id, doc.value["feed_id"], doc.value.get("last_sync")))

    return matches

def enqueue_subs(bulk_queue: BulkUpdateQueue, *subs: tuple[Subscription, str]):
    for sub, _ in subs:
        if not sub.user_id:
            raise ValueError(f"Sub {sub.title} is missing user_id")
        elif not sub.feed_id:
            raise ValueError(f"Sub {sub.title} is missing feed_id")

    for sub, rev in subs:
        if not sub.id:
            sub.id = build_key("sub", sub.user_id, sub.feed_id)
        doc = {
            "_id": sub.id,
            "doc_type": "sub",
            "content": sub.doc(),
            "updated": now_in_iso(),
        }
        if rev:
            doc["_rev"] = rev
        bulk_queue.enqueue(doc)
