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

class JsonObject:

    def __init__(self, source: dict={}):
        self._doc = { k:v for k, v in source.items() if v != None }

    def get_prop(self, name: str, default: object=None) -> object:
        return self._doc.get(name, default)

    def set_prop(self, name: str, val: object):
        if val != None:
            self._doc[name] = val
        else:
            # Delete null values
            self._doc.pop(name, None)

    def __bool__(self):
        return not not self._doc

    def as_dict(self):
        return self._doc
