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

from .entity import Entity

STATUS_OK = "ok"
STATUS_MISSING = "missing"
STATUS_FAILED = "failed"

ATTACHMENT_ORIGINAL = "original"
ATTACHMENT_DISPLAY = "display"


class Favicon(Entity):

    DOC_TYPE = "favicon"

    def __init__(self, source: dict = {}):
        super().__init__(source)
        if not source:
            self.doc_type = self.__class__.DOC_TYPE

    @property
    def feed_id(self) -> str:
        return self.get_prop("feed_id")

    @feed_id.setter
    def feed_id(self, val: str):
        self.set_prop("feed_id", val)

    @property
    def status(self) -> str:
        return self.get_prop("status")

    @status.setter
    def status(self, val: str):
        self.set_prop("status", val)

    @property
    def checked_at(self) -> float:
        return self.get_prop("checked_at")

    @checked_at.setter
    def checked_at(self, val: float):
        self.set_prop("checked_at", val)

    @property
    def source_url(self) -> str:
        return self.get_prop("source_url")

    @source_url.setter
    def source_url(self, val: str):
        self.set_prop("source_url", val)

    @property
    def content_type(self) -> str:
        return self.get_prop("content_type")

    @content_type.setter
    def content_type(self, val: str):
        self.set_prop("content_type", val)

    @property
    def source_hash(self) -> str:
        return self.get_prop("source_hash")

    @source_hash.setter
    def source_hash(self, val: str):
        self.set_prop("source_hash", val)

    @property
    def content_hash(self) -> str:
        return self.get_prop("content_hash")

    @content_hash.setter
    def content_hash(self, val: str):
        self.set_prop("content_hash", val)

    @property
    def width(self) -> int:
        return self.get_prop("width")

    @width.setter
    def width(self, val: int):
        self.set_prop("width", val)

    @property
    def height(self) -> int:
        return self.get_prop("height")

    @height.setter
    def height(self, val: int):
        self.set_prop("height", val)

    def has_display_attachment(self) -> bool:
        attachments = self._doc.get("_attachments") or {}
        return ATTACHMENT_DISPLAY in attachments

    def new_key(self) -> str | None:
        if not self.feed_id:
            raise ValueError("Missing feed id")
        return self.build_key(self.doc_type, self.feed_id)
