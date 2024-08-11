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

class SubFolder:

    def __init__(self, id: str=None, title: str=None):
        self._parent_id = None
        self._id = id
        self._title = title

    @property
    def id(self) -> str:
        return self._id

    @id.setter
    def id(self, val: str):
        self._id = val

    @property
    def title(self) -> str:
        return self._title

    @title.setter
    def title(self, val: str):
        self._title = val

    @property
    def parent_id(self) -> str:
        return self._parent_id

    @parent_id.setter
    def parent_id(self, val: str):
        self._parent_id = val
