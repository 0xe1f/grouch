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

from web.ext_type.json_object import JsonObject
import datatype

class Subscription(JsonObject):

    def __init__(self, sub: datatype.Subscription|None=None, feed: datatype.FeedContent|None=None, source: dict={}):
        super().__init__(source)
        if sub:
            self.set_prop("id", sub.id)
            self.set_prop("title", sub.title)
            self.set_prop("unread", sub.unread_count)
            self.set_prop("parent", sub.folder_id)
        if feed:
            self.set_prop("faviconUrl", feed.favicon_url)
            self.set_prop("link", feed.site_url)

    @property
    def id(self) -> str:
        return self._doc.get("id")

    @property
    def link(self) -> str:
        return self._doc.get("link")

    @property
    def title(self) -> str:
        return self._doc.get("title")

    @property
    def unread_count(self) -> int:
        return self._doc.get("unread")

    @unread_count.setter
    def unread_count(self, val: int):
        self.set_prop("unread", val)

    @property
    def favicon_url(self) -> str:
        return self._doc.get("faviconUrl")

    @property
    def folder_id(self) -> str:
        return self._doc.get("parent")
