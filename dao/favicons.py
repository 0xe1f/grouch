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
from entity.favicon import ATTACHMENT_DISPLAY
from entity.favicon import ATTACHMENT_ORIGINAL
from entity.favicon import Favicon
from couchdb.http import ResourceConflict
import logging


class FaviconDao(Dao):

    def find_by_feed_id(self, feed_id: str) -> Favicon | None:
        key = Favicon.build_key(Favicon.DOC_TYPE, feed_id)
        if key not in self.db:
            return None
        return Favicon(self.db[key])

    def find_by_id(self, favicon_id: str) -> Favicon | None:
        if favicon_id not in self.db:
            return None
        return Favicon(self.db[favicon_id])

    def get_display_bytes(self, favicon: Favicon) -> bytes | None:
        if not favicon.id or not favicon.has_display_attachment():
            return None
        handle = self.db.get_attachment(favicon.id, ATTACHMENT_DISPLAY)
        if handle is None:
            return None
        try:
            return handle.read()
        finally:
            handle.close()

    def save_meta(self, favicon: Favicon) -> Favicon:
        """Save metadata only (no attachment rewrite)."""
        doc = favicon.as_dict()
        if not doc.get("_id"):
            doc["_id"] = favicon.new_key()
        # Avoid rewriting attachment stubs with empty bodies via save.
        # CouchDB keeps existing attachments when _attachments is omitted on update
        # only if we don't strip them — keep stubs from the loaded doc.
        self.db.save(doc)
        return Favicon(doc)

    def save_with_attachments(
        self,
        favicon: Favicon,
        original: bytes,
        original_content_type: str,
        display: bytes,
    ) -> Favicon:
        """Save metadata and replace original + display attachments."""
        doc = favicon.as_dict()
        if not doc.get("_id"):
            doc["_id"] = favicon.new_key()

        # Drop attachment stubs before save; put_attachment will recreate them.
        doc.pop("_attachments", None)

        for attempt in range(2):
            try:
                self.db.save(doc)
                self.db.put_attachment(
                    doc, original, ATTACHMENT_ORIGINAL, original_content_type,
                )
                self.db.put_attachment(
                    doc, display, ATTACHMENT_DISPLAY, "image/png",
                )
                return Favicon(doc)
            except ResourceConflict:
                logging.warning(
                    "Favicon save conflict for %s (attempt %s)", doc.get("_id"), attempt + 1,
                )
                existing = self.db.get(doc["_id"])
                if not existing:
                    raise
                doc["_rev"] = existing["_rev"]

        raise RuntimeError(f"Could not save favicon {doc.get('_id')}")
