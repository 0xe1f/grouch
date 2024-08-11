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

class DatabaseConfig:

    def __init__(self, **item):
        self.__dict__.update(item)

        if not hasattr(self, "port"):
            self.port = 5984

    def validate(self):
        if not self.name:
            raise ValueError("Missing database name")
        if not self.username:
            raise ValueError("Missing database username")
        if not self.password:
            raise ValueError("Missing database password")
        if not self.host:
            raise ValueError("Missing database host")
        if not self.port:
            raise ValueError("Missing database port")
