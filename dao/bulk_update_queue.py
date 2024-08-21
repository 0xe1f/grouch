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

from couchdb.client import Database
from couchdb.http import ResourceConflict
from entity import Entity
from datetime import datetime

# Not thread-safe
class BulkUpdateQueue:

    def __init__(self, db: Database, max_size: int=40, track_ids: bool=True):
        self._max_size = max_size
        self._docs = []
        self._db = db
        self._enqueued_count = 0
        self._success_count = 0
        self._conflict_count = 0
        self._commit_count = 0
        self._success_ids = []
        self._track_ids = track_ids

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.flush()

    def enqueue(self, *objs: Entity):
        # Update update time & attach an id
        for obj in objs:
            if not obj.id:
                obj.id = obj.new_key()
            obj.updated = datetime.now().timestamp()
            self._docs.append(obj.as_dict())

        self._enqueued_count += len(objs)

        # If queue overflows, write
        if len(self._docs) > self._max_size:
            pending = self._docs[:self._max_size]
            self._docs = self._docs[self._max_size:]
            if pending:
                self._commit(pending)

    def flush(self):
        pending = self._docs
        self._docs = []
        self._commit(pending)

    @property
    def enqueued_count(self) -> int:
        return self._enqueued_count

    @property
    def written_count(self) -> int:
        return self._success_count

    @property
    def pending_count(self) -> int:
        return len(self._docs)

    @property
    def conflict_count(self) -> int:
        return self._conflict_count

    @property
    def commit_count(self) -> int:
        return self._commit_count

    def pop_written_ids(self) -> list[str]:
        if not self._track_ids:
            return []
        success_ids = self._success_ids
        self._success_ids = []
        return success_ids

    def _commit(self, docs: list):
        if not len(docs):
            # logging.debug("Nothing to write")
            return

        self._commit_count += 1
        for result in self._db.update(docs):
            success, id, status = result
            if success:
                self._success_count += 1
                if self._track_ids:
                    self._success_ids.append(id)
            elif not type(status) is ResourceConflict:
                raise status
            else:
                self._conflict_count += 1

        # logging.debug(f"Wrote {self._success_count} items; {self._conflict_count} conflicts")
