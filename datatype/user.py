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
import bcrypt

class User(FlexObject):

    DOC_TYPE = "user"

    def __init__(self, source: dict[str, str]={}):
        super().__init__(source)
        if not source:
            self.doc_type = User.DOC_TYPE

    @property
    def username(self) -> str:
        return self.get_prop("username")

    @username.setter
    def username(self, val: str):
        self.set_prop("username", val)

    @property
    def hashed_password(self) -> str:
        return self.get_prop("hashed_password")

    @hashed_password.setter
    def hashed_password(self, val: str):
        self.set_prop("hashed_password", val)

    @property
    def salt(self) -> str:
        return self.get_prop("salt")

    @salt.setter
    def salt(self, val: str):
        self.set_prop("salt", val)

    @property
    def email_address(self) -> str:
        return self.get_prop("email_address")

    @email_address.setter
    def email_address(self, val: str):
        self.set_prop("email_address", val)

    @property
    def last_sync(self) -> str:
        return self.get_prop("last_sync")

    @last_sync.setter
    def last_sync(self, val: str):
        self.set_prop("last_sync", val)

    def set_hashed_password(self, plaintext: str, salt: bytes):
        self.hashed_password = bcrypt.hashpw(plaintext.encode(), salt).hex()
        self.salt = salt.hex()

    def new_key(self) -> str|None:
        if not self.username:
            raise ValueError("Missing username")

        return build_key(self.doc_type, self.username)
