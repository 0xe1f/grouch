from common import build_key
from common import now_in_iso
from uuid import uuid4
from couchdb.http import ResourceConflict
from datatype import Folder
from store.connection import Connection

def write_folders(conn: Connection, *folders: Folder) -> list[Folder]:
    for folder in folders:
        if not folder.user_id:
            raise ValueError(f"Folder {folder.title} is missing user_id")

    docs = []
    id_map = {}
    for folder in folders:
        if not folder.id:
            folder.id = build_key("folder", uuid4().hex)
        doc = wrap_folder(folder)
        docs.append(doc)
        id_map[doc["_id"]] = folder

    results = conn.db.update(docs)
    succeeded = []

    for result in results:
        success, id, status = result
        if success:
            succeeded.append(id_map[id])
        elif not type(status) is ResourceConflict:
            raise status

    return succeeded

def find_folders_by_user_id(conn: Connection, user_id: str) -> map:
    matches = {}
    for item in conn.db.view("maint/folders-by-user", key=user_id):
        matches[item.value] = item.id

    return matches

def wrap_folder(folder: Folder) -> map:
    return {
        "_id": build_key("folder", folder.id),
        "doc_type": "folder",
        "content": folder.doc(),
        "updated": now_in_iso(),
    }
