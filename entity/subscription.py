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
from .user import User

class Subscription(Entity):

    DOC_TYPE = "sub"

    def __init__(self, source: dict={}):
        super().__init__(source)
        if not source:
            self.doc_type = __class__.DOC_TYPE
            self.unread_count = 0

    @property
    def title(self) -> str:
        return self.get_prop("title")

    @title.setter
    def title(self, val: str):
        self.set_prop("title", val)

    @property
    def unread_count(self) -> str:
        return self.get_prop("unread_count")

    @unread_count.setter
    def unread_count(self, val: str):
        self.set_prop("unread_count", val)

    @property
    def subscribed(self) -> int:
        return self.get_prop("subscribed")

    @subscribed.setter
    def subscribed(self, val: int):
        self.set_prop("subscribed", val)

    @property
    def feed_id(self) -> str:
        return self.get_prop("feed_id")

    @feed_id.setter
    def feed_id(self, val: str):
        self.set_prop("feed_id", val)

    @property
    def folder_id(self) -> str:
        return self.get_prop("folder_id")

    @folder_id.setter
    def folder_id(self, val: str):
        self.set_prop("folder_id", val)

    @property
    def last_synced(self) -> int:
        return self.get_prop("last_synced")

    @last_synced.setter
    def last_synced(self, val: int):
        self.set_prop("last_synced", val)

    @property
    def user_id(self) -> str:
        return self.get_prop("user_id")

    @user_id.setter
    def user_id(self, val: str):
        self.set_prop("user_id", val)

    def new_key(self) -> str|None:
        if not self.user_id:
            raise ValueError("Missing user id")
        if not self.feed_id:
            raise ValueError("Missing entry feed id")

        return self.build_key(self.doc_type, self.user_id, self.feed_id)

    @classmethod
    def extract_owner_id(cls, obj_id: str) -> str|None:
        doc_type, parts = __class__.decompose_key(obj_id)
        if doc_type != __class__.DOC_TYPE:
            return None
        if len(parts) != 2:
            return None
        return __class__.build_key(User.DOC_TYPE, parts[0])
