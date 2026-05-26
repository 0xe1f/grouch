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

from tests.test_dao import TestDao
from entity import Invite
import time
import random

class TestDaoInvites(TestDao):

    @property
    def invites(self):
        return self.dao.invites

    # -------------------------------------------------------------------------
    # Helpers

    def _make_invite(
        self,
        invitee_email: str = None,
        status: str = Invite.STATUS_PENDING,
        sent_at: float = None,
        expiry_date: float = None,
    ) -> Invite:
        invite = Invite()
        invite.inviter_user_id = f"user::{self.random_string()}"
        invite.invitee_email = invitee_email or f"{self.random_string()}@example.com"
        invite.status = status
        invite.sent_at = sent_at or time.time()
        invite.expiry_date = expiry_date or (time.time() + 14 * 86400)
        self.assertTrue(self.invites.create(invite))
        return invite

    # -------------------------------------------------------------------------
    # create / find_by_token

    def test_create_and_find_by_token(self):
        invite = self._make_invite()
        loaded = self.invites.find_by_token(invite.token)
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.token, invite.token)
        self.assertEqual(loaded.invitee_email, invite.invitee_email)
        self.assertEqual(loaded.status, Invite.STATUS_PENDING)

    def test_find_by_token_not_found(self):
        self.assertIsNone(self.invites.find_by_token("nonexistent-token"))

    def test_id_format(self):
        invite = self._make_invite()
        self.assertTrue(invite.id.startswith("invite::"))
        self.assertIn(invite.token, invite.id)

    # -------------------------------------------------------------------------
    # find_by_invitee_email

    def test_find_by_invitee_email(self):
        email = f"{self.random_string()}@example.com"
        invite = self._make_invite(invitee_email=email)
        results = self.invites.find_by_invitee_email(email)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].invitee_email, email)

    def test_find_by_invitee_email_no_match(self):
        results = self.invites.find_by_invitee_email("nobody@example.com")
        self.assertEqual(results, [])

    def test_find_by_invitee_email_multiple(self):
        email = f"{self.random_string()}@example.com"
        self._make_invite(invitee_email=email, status=Invite.STATUS_PENDING)
        self._make_invite(invitee_email=email, status=Invite.STATUS_CANCELLED)
        results = self.invites.find_by_invitee_email(email)
        self.assertEqual(len(results), 2)

    # -------------------------------------------------------------------------
    # get_page_by_status

    def test_get_page_by_status_pending(self):
        email = f"{self.random_string()}@example.com"
        self._make_invite(invitee_email=email, status=Invite.STATUS_PENDING)
        self._make_invite(invitee_email=email, status=Invite.STATUS_EXPIRED)

        pending, next_start = self.invites.get_page_by_status(Invite.STATUS_PENDING)
        statuses = [i.status for i in pending]
        self.assertIn(Invite.STATUS_PENDING, statuses)
        self.assertNotIn(Invite.STATUS_EXPIRED, statuses)

    def test_get_page_by_status_pagination(self):
        for _ in range(5):
            self._make_invite(status=Invite.STATUS_CANCELLED)

        page1, next_start = self.invites.get_page_by_status(
            Invite.STATUS_CANCELLED, limit=3
        )
        self.assertEqual(len(page1), 3)
        self.assertIsNotNone(next_start)

        page2, next_start2 = self.invites.get_page_by_status(
            Invite.STATUS_CANCELLED, start=next_start, limit=3
        )
        self.assertGreaterEqual(len(page2), 2)
        # No overlap between pages
        ids1 = {i.id for i in page1}
        ids2 = {i.id for i in page2}
        self.assertEqual(ids1 & ids2, set())

    # -------------------------------------------------------------------------
    # get_page_all

    def test_get_page_all(self):
        for _ in range(3):
            self._make_invite()

        invites, _ = self.invites.get_page_all()
        self.assertGreaterEqual(len(invites), 3)

    # -------------------------------------------------------------------------
    # find_expired_pending

    def test_find_expired_pending(self):
        past_expiry = time.time() - 3600
        future_expiry = time.time() + 3600

        expired_invite = self._make_invite(expiry_date=past_expiry)
        active_invite = self._make_invite(expiry_date=future_expiry)

        results = self.invites.find_expired_pending(before_timestamp=time.time())
        result_ids = {i.id for i in results}

        self.assertIn(expired_invite.id, result_ids)
        self.assertNotIn(active_invite.id, result_ids)

    def test_find_expired_pending_excludes_non_pending(self):
        past_expiry = time.time() - 3600
        already_expired = self._make_invite(
            expiry_date=past_expiry, status=Invite.STATUS_EXPIRED
        )

        results = self.invites.find_expired_pending(before_timestamp=time.time())
        result_ids = {i.id for i in results}
        self.assertNotIn(already_expired.id, result_ids)

    # -------------------------------------------------------------------------
    # update

    def test_update_status(self):
        invite = self._make_invite()
        invite.status = Invite.STATUS_CANCELLED
        self.invites.update(invite)

        loaded = self.invites.find_by_token(invite.token)
        self.assertEqual(loaded.status, Invite.STATUS_CANCELLED)
