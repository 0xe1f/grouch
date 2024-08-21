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
from entity import Folder

class FolderDao(Dao):

    BY_USER = "maint/folders_by_user"

    def find_by_id(
        self,
        *ids: str,
    ) -> list[Folder]:
        matches = []
        for item in self.db.view(self.__class__.ALL_DOCS, keys=ids, include_docs=True):
            if "doc" in item:
                matches.append(Folder(item.doc))

        return matches

    def find_by_user(
        self,
        user_id: str,
    ) -> list[Folder]:
        matches = []
        for item in self.db.view(self.__class__.BY_USER, key=user_id, include_docs=True):
            matches.append(Folder(item.doc))

        return matches
