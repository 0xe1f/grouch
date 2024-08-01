from common import now_in_iso
from common import build_key
from datatype import Subscription
from store import BulkUpdateQueue

def enqueue_subs(bulk_queue: BulkUpdateQueue, *subs: tuple[Subscription, str]):
    for sub, _ in subs:
        if not sub.user_id:
            raise ValueError(f"Sub {sub.title} is missing user_id")
        elif not sub.feed_id:
            raise ValueError(f"Sub {sub.title} is missing feed_id")

    now_iso = now_in_iso()
    for sub, rev in subs:
        if not sub.id:
            sub.id = build_key("sub", sub.user_id, sub.feed_id)
        doc = {
            "_id": sub.id,
            "doc_type": "sub",
            "content": sub.doc(),
            "updated": now_iso,
        }
        if rev:
            doc["_rev"] = rev
        bulk_queue.enqueue(doc)
