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

from .dao import Dao
from entity import Entry

class EntryDao(Dao):

    BY_FEED = "maint/entries_by_feed"

    def find_by_id(
        self,
        *entry_ids: str,
    ) -> list[Entry]:
        matches = []
        for item in self.db.view(self.__class__.ALL_DOCS, keys=entry_ids, include_docs=True):
            if doc := item.get("doc"):
                matches.append(Entry(doc))

        return matches

    def iter_updated_since(
        self,
        feed_id: str,
        updated_min: str,
    ):
        options = {
            "start_key": [ feed_id, updated_min ],
            "end_key": [ feed_id, {} ],
            "include_docs": True,
        }
        for item in self.db.view("maint/entries_by_feed_updated", **options):
            yield Entry(item["doc"])

    def iter_by_uid(
        self,
        feed_id: str,
        *entry_uids: str,
    ):
        options = {
            "include_docs": True,
            "keys": [[feed_id, entry_uid] for entry_uid in entry_uids],
        }
        for item in self.db.view(self.__class__.BY_FEED, **options):
            yield Entry(item["doc"])
