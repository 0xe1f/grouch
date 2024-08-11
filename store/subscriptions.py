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

def generate_subscriptions_by_folder(conn: Connection, folder_id: str, batch_size: int=40):
    options = {
        "key": folder_id,
        "descending": True,
        "include_docs": True,
    }
    for item in conn.db.iterview(views.SUBS_BY_FOLDER, batch_size, **options):
        yield Subscription(item.doc)

def generate_subscriptions_by_user(conn: Connection, user_id: str, batch_size: int=40):
    options = {
        "end_key": [ user_id ],
        "start_key":[ user_id, {}],
        "descending": True,
        "include_docs": True,
    }
    for item in conn.db.iterview(views.SUBS_BY_USER, batch_size, **options):
        yield Subscription(item.doc)
