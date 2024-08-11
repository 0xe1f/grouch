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
