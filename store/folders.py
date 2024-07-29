from common import format_iso
from datatype import Folder
from store import Connection
from time import gmtime
import logging


def create_folder(conn: Connection, folder: Folder) -> bool:
    if not folder.user_id:
        logging.error("Folder missing user_id")
        return False
    elif not folder.id:
        logging.error("Folder missing id")
        return False

    item_id = folder_id(folder)
    doc = {
        "_id": item_id,
        "doc_type": "folder",
        "content": folder.doc(),
        "updated": format_iso(gmtime()),
    }

    conn.db[item_id] = doc

    return True


def folder_id(folder: Folder) -> str:
    return f"folder::{folder.id}"
