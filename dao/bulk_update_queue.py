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

    DEFAULT_MAX=40

    def __init__(
        self,
        db: Database,
        max_size: int=DEFAULT_MAX,
        track_ids: bool=True,
    ):
        self._max_size = max_size
        self._entities = []
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
            self._entities.append(obj)

        self._enqueued_count += len(objs)

        # If queue overflows, write
        if len(self._entities) > self._max_size:
            pending = self._entities[:self._max_size]
            self._entities = self._entities[self._max_size:]
            if pending:
                self._commit(pending)

    def flush(self):
        pending = self._entities
        self._entities = []
        self._commit(pending)

    @property
    def enqueued_count(self) -> int:
        return self._enqueued_count

    @property
    def written_count(self) -> int:
        return self._success_count

    @property
    def pending_count(self) -> int:
        return len(self._entities)

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

    def _commit(self, entities: list[Entity]):
        if not len(entities):
            # logging.debug("Nothing to write")
            return

        self._commit_count += 1

        docs = []
        map = {}
        for entity in entities:
            if not entity.id:
                entity.id = entity.new_key()
            entity.updated = datetime.now().timestamp()
            docs.append(entity.as_dict())
            map[entity.id] = entity

        for result in self._db.update(docs):
            success, id, status = result
            if success:
                map[id].rev = status
                self._success_count += 1
                if self._track_ids:
                    self._success_ids.append(id)
            elif not type(status) is ResourceConflict:
                raise status
            else:
                self._conflict_count += 1

        # logging.debug(f"Wrote {self._success_count} items; {self._conflict_count} conflicts")
