from datatype import Subscription
from store import Connection
from store import views

def find_subs_by_id(conn: Connection, *ids: str) -> list[Subscription]:
    matches = []
    for item in conn.db.view(views.ALL_DOCS, keys=ids, include_docs=True):
        if "doc" in item:
            matches.append(Subscription(item["doc"]))

    return matches

def find_sub_ids_by_folder(conn: Connection, folder_id: str) -> list[str]:
    matches = []
    for item in conn.db.view(views.SUBS_BY_FOLDER, key=folder_id):
        matches.append(item.id)

    return matches

def find_subs_by_user(conn: Connection, user_id: str) -> list[Subscription]:
    matches = []
    for item in conn.db.view(views.SUBS_BY_USER, start_key=[ user_id ], end_key=[ user_id, {} ], include_docs=True):
        matches.append(Subscription(item.doc))

    return matches

def find_user_subs_synced(conn: Connection, user_id: str) -> list[tuple[str, str, str]]:
    matches = []
    for doc in conn.db.view(views.SUBS_BY_USER_BY_SYNC, start_key=[ user_id ], end_key=[ user_id, {} ]):
        matches.append((doc.id, doc.value["feed_id"], doc.value.get("folder_id"), doc.value.get("last_sync")))

    return matches
