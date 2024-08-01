from couchdb.http import ResourceConflict
from store.connection import Connection
import logging

# Not thread-safe
class BulkUpdateQueue:

    def __init__(self, conn: Connection, size: int=40):
        self._size = size
        self._docs = []
        self._items = {}
        self._conn = conn
        self._success_count = 0
        self._conflict_count = 0
        self._success_items = []

    def enqueue(self, *docs: dict):
        self.enqueue_tuple(*[(doc, None) for doc in docs])

    def enqueue_tuple(self, *docs: tuple[dict, object]):
        for doc, item in docs:
            self._docs.append(doc)
            if item:
                self._items[doc["_id"]] = item
        if len(self._docs) > self._size:
            # logging.debug(f"Element count {len(self._docs)} exceeded max size {self._size}; writing...")
            pending = self._docs[:self._size]
            self._docs = self._docs[self._size:]
            self._bulk_write(pending)

    def flush(self):
        pending = self._docs.copy()
        self._docs.clear()
        self._bulk_write(pending)

    @property
    def write_ok(self) -> int:
        return self._success_count

    @property
    def write_conflict(self) -> int:
        return self._conflict_count

    def successful_items(self) -> list:
        success = self._success_items.copy()
        self._success_items.clear()
        return success

    def reset(self):
        self._docs.clear()
        self._items.clear()
        self._success_items.clear()
        self._success_count = 0
        self._conflict_count = 0

    def _bulk_write(self, docs: list):
        if not len(docs):
            # logging.debug("Nothing to write")
            return

        results = self._conn.db.update(docs)
        for result in results:
            success, id, status = result
            item = self._items.pop(id, None)
            if success:
                self._success_count += 1
                if item:
                    self._success_items.append(item)
            elif not type(status) is ResourceConflict:
                raise status
            else:
                self._conflict_count += 1

        # logging.debug(f"Done writing; {self._success_count} OK, {self._conflict_count} have conflicts")
