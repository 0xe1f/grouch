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
from datatype import Subscription

class SubscriptionDao(Dao):

    BY_FOLDER = "maint/subs_by_folder"
    BY_USER = "maint/subs_by_user"
    BY_USER_BY_SYNC = "maint/subs_by_user"

    def find_by_id(
        self,
        *ids: str,
    ) -> list[Subscription]:
        matches = []
        for item in self.db.view(self.__class__.ALL_DOCS, keys=ids, include_docs=True):
            if "doc" in item:
                matches.append(Subscription(item["doc"]))

        return matches

    def find_ids_by_folder(
        self,
        folder_id: str,
    ) -> list[str]:
        matches = []
        for item in self.db.view(self.__class__.BY_FOLDER, key=folder_id):
            matches.append(item.id)

        return matches

    def find_by_user(
        self,
        user_id: str,
    ) -> list[Subscription]:
        options = {
            "start_key": [ user_id ],
            "end_key": [ user_id, {} ],
            "include_docs": True,
        }
        matches = []
        for item in self.db.view(self.__class__.BY_USER, **options):
            matches.append(Subscription(item.doc))

        return matches

    def find_metadata_by_user_by_synced(
        self,
        user_id: str,
    ) -> list[tuple[str, str, str]]:
        matches = []
        for doc in self.db.view(self.__class__.BY_USER_BY_SYNC, start_key=[ user_id ], end_key=[ user_id, {} ]):
            matches.append((doc.id, doc.value["feed_id"], doc.value.get("folder_id"), doc.value.get("last_sync")))

        return matches

    def iter_by_folder(
        self,
        folder_id: str,
        batch_size: int=40,
    ):
        options = {
            "key": folder_id,
            "descending": True,
            "include_docs": True,
        }
        for item in self.db.iterview(self.__class__.BY_FOLDER, batch_size, **options):
            yield Subscription(item.doc)

    def iter_by_user(
        self,
        user_id: str,
        batch_size: int=40,
    ):
        options = {
            "end_key": [ user_id ],
            "start_key":[ user_id, {}],
            "descending": True,
            "include_docs": True,
        }
        for item in self.db.iterview(self.__class__.BY_USER, batch_size, **options):
            yield Subscription(item.doc)
