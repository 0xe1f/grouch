from datatype import FlexObject
from couchdb.http import ResourceConflict
from store.connection import Connection
import logging

# Not thread-safe
class BulkUpdateQueue:

    def __init__(self, conn: Connection, size: int=40):
        self._size = size
        self._docs = []
        self._conn = conn
        self._enqueued_count = 0
        self._success_count = 0
        self._conflict_count = 0
        self._success_ids = []

    def __enter__(self):
        return self

    def __exit__(self, type, value, tb):
        self.flush()

    def enqueue_flex(self, *objs: FlexObject):
        self._docs.extend([obj.as_dict() for obj in objs])
        pending = []
        if len(self._docs) > self._size:
            pending = self._docs[:self._size]
            self._docs = self._docs[self._size:]

        self._enqueued_count += len(objs)
        if pending:
            self._bulk_write(pending)

    def flush(self):
        pending = self._docs.copy()
        self._docs.clear()
        self._bulk_write(pending)

    @property
    def enqueued_count(self) -> int:
        return self._enqueued_count

    @property
    def written_count(self) -> int:
        return self._success_count

    @property
    def conflict_count(self) -> int:
        return self._conflict_count

    def pop_written_ids(self) -> list[str]:
        success_ids = self._success_ids
        self._success_ids = []
        return success_ids

    def _bulk_write(self, docs: list):
        if not len(docs):
            # logging.debug("Nothing to write")
            return

        for result in self._conn.db.update(docs):
            success, id, status = result
            if success:
                self._success_count += 1
                self._success_ids.append(id)
            elif not type(status) is ResourceConflict:
                raise status
            else:
                self._conflict_count += 1

        # logging.debug(f"Wrote {self._success_count} items; {self._conflict_count} conflicts")
