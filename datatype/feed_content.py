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

class FeedContent(FlexObject):

    def __init__(self, source: dict[str, str]={}):
        super().__init__(source)
        if not source:
            self.doc_type = "feed"
        self._computed_digest = None

    @property
    def feed_url(self) -> str:
        return self.get_prop("feed_url")

    @feed_url.setter
    def feed_url(self, val: str):
        self.set_prop("feed_url", val)
        self._computed_digest = None

    @property
    def title(self) -> str:
        return self.get_prop("title")

    @title.setter
    def title(self, val: str):
        self.set_prop("title", val)
        self._computed_digest = None

    @property
    def description(self) -> str:
        return self.get_prop("description")

    @description.setter
    def description(self, val: str):
        self.set_prop("description", val)
        self._computed_digest = None

    @property
    def favicon_url(self) -> str:
        return self.get_prop("favicon_url")

    @favicon_url.setter
    def favicon_url(self, val: str):
        self.set_prop("favicon_url", val)
        self._computed_digest = None

    @property
    def site_url(self) -> str:
        return self.get_prop("site_url")

    @site_url.setter
    def site_url(self, val: str):
        self.set_prop("site_url", val)
        self._computed_digest = None

    @property
    def published(self) -> str:
        return self.get_prop("published")

    @published.setter
    def published(self, val: str):
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
            hash_keys = [ "feed_url", "title", "description", "favicon_url", "site_url", "published" ]
            hash_doc = { key:self._doc[key] for key in hash_keys if key in self._doc }
            m = hashlib.md5()
            m.update(json.dumps(hash_doc).encode())
            self._computed_digest = m.hexdigest()

        return self._computed_digest

    def new_key(self) -> str|None:
        if not self.feed_url:
            raise ValueError("Missing feed URL")

        return build_key(self.doc_type, self.feed_url)
