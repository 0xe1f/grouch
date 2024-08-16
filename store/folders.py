# Copyright (C) 2024 Akop Karapetyan
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from common import build_key
from datetime import datetime
from uuid import uuid4
from couchdb.http import ResourceConflict
from datatype import Folder
from store.connection import Connection
from store import views

def find_folders_by_id(conn: Connection, *ids: str) -> list[Folder]:
    matches = []
    for item in conn.db.view(views.ALL_DOCS, keys=ids, include_docs=True):
        if "doc" in item:
            matches.append(Folder(item["doc"]))

    return matches

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

def find_folders_by_user(conn: Connection, user_id: str) -> list[Folder]:
    matches = []
    for item in conn.db.view(views.FOLDERS_BY_USER, key=user_id, include_docs=True):
        matches.append(Folder(item.doc))

    return matches

def wrap_folder(folder: Folder) -> map:
    return {
        "_id": build_key("folder", folder.id),
        "doc_type": "folder",
        "content": folder.as_dict(),
        "updated": datetime.now().timestamp(),
    }
