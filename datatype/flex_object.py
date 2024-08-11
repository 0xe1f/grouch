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

from common import decompose_key

class FlexObject:

    def __init__(self, source: dict[str, str]={}):
        self._doc = source.copy()

    @property
    def id(self) -> str:
        return self.get_prop("_id")

    @id.setter
    def id(self, val: str):
        self.set_prop("_id", val)

    @property
    def rev(self) -> str:
        return self.get_prop("_rev")

    @rev.setter
    def rev(self, val: str):
        self.set_prop("_rev", val)

    @property
    def updated(self) -> str:
        return self.get_prop("updated")

    @updated.setter
    def updated(self, val: str):
        self.set_prop("updated", val)

    @property
    def doc_type(self) -> str:
        return self.get_prop("doc_type")

    @doc_type.setter
    def doc_type(self, val: str):
        self.set_prop("doc_type", val)

    def get_prop(self, name: str) -> object:
        return self._doc.get(name)

    def set_prop(self, name: str, val: object|None):
        if val != None:
            self._doc[name] = val
        else:
            # Delete null values
            self._doc.pop(name, None)

    def new_key(self) -> str|None:
        return None

    def as_dict(self):
        return self._doc.copy()

    def mark_deleted(self):
        self._doc = {
            "_id": self._doc["_id"],
            "_rev": self._doc["_rev"],
            "_deleted": True,
        }

    @staticmethod
    def extract_doc_type(obj_id: str) -> str|None:
        doc_type, _ = decompose_key(obj_id)
        return doc_type
