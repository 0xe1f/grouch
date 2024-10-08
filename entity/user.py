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
import bcrypt
import secrets

class User(Entity):

    DOC_TYPE = "user"

    def __init__(self, source: dict={}):
        super().__init__(source)
        if not source:
            self.doc_type = self.__class__.DOC_TYPE
            self.uid = secrets.token_urlsafe(12)

    @property
    def uid(self) -> str:
        return self._doc.get("uid")

    @uid.setter
    def uid(self, val: str):
        self._doc["uid"] = val
        self.id = None

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
    def email_address(self) -> str:
        return self.get_prop("email_address")

    @email_address.setter
    def email_address(self, val: str):
        self.set_prop("email_address", val)

    @property
    def last_sync(self) -> int:
        return self.get_prop("last_sync")

    @last_sync.setter
    def last_sync(self, val: int):
        self.set_prop("last_sync", val)

    @property
    def created(self) -> int:
        return self.get_prop("created")

    @created.setter
    def created(self, val: int):
        self.set_prop("created", val)

    def set_hashed_password(self, plaintext: str, salt: bytes):
        self.hashed_password = bcrypt.hashpw(plaintext.encode(), salt).hex()

    def plaintext_matching_stored(self, plaintext: str) -> bool:
        return bcrypt.checkpw(plaintext.encode(), bytes.fromhex(self.hashed_password))

    def new_key(self) -> str|None:
        return self.build_key(self.doc_type, self.uid)
