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

class Article(Entity):

    PROP_UNREAD = "unread"
    PROP_LIKED = "like"
    PROP_STARRED = "star"

    DOC_TYPE = "article"

    def __init__(self, source: dict={}):
        super().__init__(source)
        if not source:
            self.doc_type = Article.DOC_TYPE
        if self.tags == None:
            self.tags = []
        if self.props == None:
            self.props = []

    @property
    def user_id(self) -> str:
        return self.get_prop("user_id")

    @user_id.setter
    def user_id(self, val: str):
        self.set_prop("user_id", val)

    @property
    def entry_id(self) -> str:
        return self.get_prop("entry_id")

    @entry_id.setter
    def entry_id(self, val: str):
        self.set_prop("entry_id", val)

    @property
    def folder_id(self) -> str:
        return self.get_prop("folder_id")

    @folder_id.setter
    def folder_id(self, val: str):
        self.set_prop("folder_id", val)

    @property
    def subscription_id(self) -> str:
        return self.get_prop("subscription_id")

    @subscription_id.setter
    def subscription_id(self, val: str):
        self.set_prop("subscription_id", val)

    @property
    def tags(self) -> list[str]:
        return self.get_prop("tags")

    @tags.setter
    def tags(self, val: list[str]):
        self.set_prop("tags", val)

    @property
    def props(self) -> list[str]:
        return self.get_prop("props")

    @props.setter
    def props(self, val: list[str]):
        self.set_prop("props", val)

    def toggle_prop(self, name: str, is_set: bool|None=None):
        if is_set == None:
            if name in self.props:
                self.props.remove(name)
            else:
                self.props.append(name)
        elif is_set and name not in self.props:
            self.props.append(name)
        elif not is_set and name in self.props:
            self.props.remove(name)

    @property
    def published(self) -> int:
        return self.get_prop("published")

    @published.setter
    def published(self, val: int):
        self.set_prop("published", val)

    @property
    def synced(self) -> int:
        return self.get_prop("synced")

    @synced.setter
    def synced(self, val: int):
        self.set_prop("synced", val)

    def new_key(self) -> str|None:
        if not self.user_id:
            raise ValueError("Missing user id")
        if not self.entry_id:
            raise ValueError("Missing entry id")

        return self.build_key(self.doc_type, self.user_id, self.entry_id)

    @classmethod
    def extract_owner_id(cls, obj_id: str) -> str|None:
        doc_type, parts = __class__.decompose_key(obj_id)
        if doc_type != __class__.DOC_TYPE:
            return None
        if len(parts) != 3:
            return None
        return __class__.build_key(User.DOC_TYPE, parts[0])
