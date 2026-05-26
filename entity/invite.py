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
import secrets

class Invite(Entity):

    DOC_TYPE = "invite"

    STATUS_PENDING   = "pending"
    STATUS_ACCEPTED  = "accepted"
    STATUS_EXPIRED   = "expired"
    STATUS_CANCELLED = "cancelled"

    def __init__(self, source: dict={}):
        super().__init__(source)
        if not source:
            self.doc_type = self.__class__.DOC_TYPE
            self.token = secrets.token_urlsafe(32)

    @property
    def token(self) -> str:
        return self.get_prop("token")

    @token.setter
    def token(self, val: str):
        self.set_prop("token", val)
        self.id = None

    @property
    def inviter_user_id(self) -> str:
        return self.get_prop("inviter_user_id")

    @inviter_user_id.setter
    def inviter_user_id(self, val: str):
        self.set_prop("inviter_user_id", val)

    @property
    def invitee_email(self) -> str:
        return self.get_prop("invitee_email")

    @invitee_email.setter
    def invitee_email(self, val: str):
        self.set_prop("invitee_email", val)

    @property
    def status(self) -> str:
        return self.get_prop("status")

    @status.setter
    def status(self, val: str):
        self.set_prop("status", val)

    @property
    def sent_at(self) -> float:
        return self.get_prop("sent_at")

    @sent_at.setter
    def sent_at(self, val: float):
        self.set_prop("sent_at", val)

    @property
    def expiry_date(self) -> float:
        return self.get_prop("expiry_date")

    @expiry_date.setter
    def expiry_date(self, val: float):
        self.set_prop("expiry_date", val)

    @property
    def accepted_at(self) -> float:
        return self.get_prop("accepted_at")

    @accepted_at.setter
    def accepted_at(self, val: float):
        self.set_prop("accepted_at", val)

    @property
    def accepted_user_id(self) -> str:
        return self.get_prop("accepted_user_id")

    @accepted_user_id.setter
    def accepted_user_id(self, val: str):
        self.set_prop("accepted_user_id", val)

    def new_key(self) -> str | None:
        return self.build_key(self.doc_type, self.token)
