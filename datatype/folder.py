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
from common import decompose_key
from datatype.flex_object import FlexObject
from datatype.user import User
from uuid import uuid4

class Folder(FlexObject):

    DOC_TYPE = "folder"

    def __init__(self, source: dict={}):
        super().__init__(source)
        if not source:
            self.doc_type = __class__.DOC_TYPE
            self.uid = uuid4().hex

    @property
    def uid(self) -> str:
        return self._doc.get("uid")

    @uid.setter
    def uid(self, val: str):
        self._doc["uid"] = val

    @property
    def title(self) -> str:
        return self._doc.get("title")

    @title.setter
    def title(self, val: str):
        self._doc["title"] = val

    @property
    def user_id(self) -> int:
        return self._doc.get("user_id")

    @user_id.setter
    def user_id(self, val: int):
        self._doc["user_id"] = val

    def new_key(self) -> str|None:
        return build_key(self.doc_type, self.user_id, self.uid)

    @staticmethod
    def extract_owner_id(obj_id: str) -> str|None:
        doc_type, parts = decompose_key(obj_id)
        if doc_type != __class__.DOC_TYPE:
            return None
        if len(parts) != 2:
            return None
        return build_key(User.DOC_TYPE, parts[0])
