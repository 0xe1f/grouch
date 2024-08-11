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
import http

class Error(JsonObject):

    def __init__(self, message: str):
        super().__init__({})
        self.set_prop("message", message)

    @property
    def message(self) -> str:
        return self.get_prop("message")

    def as_dict(self):
        return super().as_dict(), http.HTTPStatus.BAD_REQUEST
