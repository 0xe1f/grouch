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

from .bulk_update_queue import BulkUpdateQueue
import couchdb.client as couchdb

class Dao:

    ALL_DOCS = "_all_docs"

    def __init__(self, db: couchdb.Database):
        self._db = db

    @property
    def db(self) -> couchdb.Database:
        return self._db

    def delete_by_id(self, id: str):
        del self._db[id]

    def new_q(
        self,
        max_size: int=BulkUpdateQueue.DEFAULT_MAX,
        track_ids: bool=False,
    ) -> BulkUpdateQueue:
        return BulkUpdateQueue(self._db, max_size, track_ids=track_ids)
