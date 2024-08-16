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

from common import build_key
from datatype.flex_object import FlexObject
import hashlib
import json

class EntryContent(FlexObject):

    def __init__(self, source: dict={}):
        super().__init__(source)
        if not source:
            self.doc_type = "entry"
        self._computed_digest = None

    @property
    def feed_id(self) -> str:
        return self.get_prop("feed_id")

    @feed_id.setter
    def feed_id(self, val: str):
        self.set_prop("feed_id", val)

    @property
    def entry_uid(self) -> str:
        return self.get_prop("entry_uid")

    @entry_uid.setter
    def entry_uid(self, val: str):
        self.set_prop("entry_uid", val)
        self._computed_digest = None

    @property
    def title(self) -> str:
        return self.get_prop("title")

    @title.setter
    def title(self, val: str):
        self.set_prop("title", val)
        self._computed_digest = None

    @property
    def author(self) -> str:
        return self.get_prop("author")

    @author.setter
    def author(self, val: str):
        self.set_prop("author", val)
        self._computed_digest = None

    @property
    def link(self) -> str:
        return self.get_prop("link")

    @link.setter
    def link(self, val: str):
        self.set_prop("link", val)
        self._computed_digest = None

    @property
    def text_body(self) -> str:
        return self.get_prop("text_body")

    @text_body.setter
    def text_body(self, val: str):
        self.set_prop("text_body", val)
        self._computed_digest = None

    @property
    def text_summary(self) -> str:
        return self.get_prop("text_summary")

    @text_summary.setter
    def text_summary(self, val: str):
        self.set_prop("text_summary", val)
        self._computed_digest = None

    @property
    def published(self) -> int:
        return self.get_prop("published")

    @published.setter
    def published(self, val: int):
        self.set_prop("published", val)
        self._computed_digest = None

    @property
    def digest(self) -> str:
        return self.get_prop("digest")

    @digest.setter
    def digest(self, val: str):
        self.set_prop("digest", val)

    def computed_digest(self):
        if not self._computed_digest:
            hash_keys = [ "entry_uid", "title", "author", "link", "text_body", "text_summary", "published" ]
            hash_doc = { key:self._doc[key] for key in hash_keys if key in self._doc }
            m = hashlib.md5()
            m.update(json.dumps(hash_doc).encode())
            self._computed_digest = m.hexdigest()

        return self._computed_digest

    def new_key(self) -> str|None:
        if not self.feed_id:
            raise ValueError("Missing feed id")
        if not self.entry_uid:
            raise ValueError("Missing entry uid")

        return build_key(self.doc_type, self.feed_id, self.entry_uid)
