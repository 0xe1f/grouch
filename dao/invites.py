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

from .dao import Dao
from entity import Invite
from datetime import datetime

PAGE_SIZE_DEFAULT = 40

class InviteDao(Dao):

    BY_STATUS_SENT    = "maint/invites_by_status_sent"
    BY_SENT           = "maint/invites_by_sent"
    BY_INVITEE_EMAIL  = "maint/invites_by_invitee_email"
    PENDING_BY_EXPIRY = "maint/invites_pending_by_expiry"

    def find_by_token(
        self,
        token: str,
    ) -> Invite | None:
        doc_id = Invite.build_key(Invite.DOC_TYPE, token)
        for item in self.db.view(self.__class__.ALL_DOCS, key=doc_id, include_docs=True):
            if item.doc and item.doc.get("doc_type") == Invite.DOC_TYPE:
                return Invite(item.doc)
        return None

    def find_by_invitee_email(
        self,
        email: str,
    ) -> list[Invite]:
        matches = []
        for item in self.db.view(
            self.__class__.BY_INVITEE_EMAIL,
            key=email,
            include_docs=True,
            reduce=False,
        ):
            if item.doc:
                matches.append(Invite(item.doc))
        return matches

    def get_page_by_status(
        self,
        status: str,
        start: list | None = None,
        limit: int = PAGE_SIZE_DEFAULT,
    ) -> tuple[list[Invite], list | None]:
        options = {
            "start_key": start if start else [status, {}],
            "end_key": [status],
            "include_docs": True,
            "limit": limit + 1,
            "descending": True,
            "reduce": False,
        }
        next_start = None
        matches = []
        for item in self.db.view(self.__class__.BY_STATUS_SENT, **options):
            if len(matches) < limit:
                matches.append(Invite(item.doc))
            else:
                next_start = item.key
                break
        return matches, next_start

    def get_page_all(
        self,
        start: float | None = None,
        limit: int = PAGE_SIZE_DEFAULT,
    ) -> tuple[list[Invite], float | None]:
        options = {
            "start_key": start if start is not None else {},
            "include_docs": True,
            "limit": limit + 1,
            "descending": True,
            "reduce": False,
        }
        next_start = None
        matches = []
        for item in self.db.view(self.__class__.BY_SENT, **options):
            if len(matches) < limit:
                matches.append(Invite(item.doc))
            else:
                next_start = item.key
                break
        return matches, next_start

    def find_expired_pending(
        self,
        before_timestamp: float,
    ) -> list[Invite]:
        options = {
            "startkey": 0,
            "endkey": before_timestamp,
            "include_docs": True,
            "reduce": False,
        }
        matches = []
        for item in self.db.view(self.__class__.PENDING_BY_EXPIRY, **options):
            if item.doc:
                matches.append(Invite(item.doc))
        return matches

    def create(
        self,
        invite: Invite,
    ) -> bool:
        if not invite.id:
            invite.id = invite.new_key()
        now = datetime.now().timestamp()
        invite.updated = now
        _, rev = self.db.save(invite.as_dict())
        if rev:
            invite.rev = rev
            return True
        return False

    def update(
        self,
        invite: Invite,
    ):
        invite.updated = datetime.now().timestamp()
        _, rev = self.db.save(invite.as_dict())
        if rev:
            invite.rev = rev
