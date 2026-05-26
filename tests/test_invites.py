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

from entity import Invite
from tasks.actions import ActionError
from tasks.actions import INVITE_INVALID_MESSAGE
from tasks.actions import invites_validate
from tests.test_dao import TestDao
import time
import unittest


class TestInviteEntity(unittest.TestCase):
    """Unit tests for the Invite entity (no DB required)."""

    def test_doc_type(self):
        invite = Invite()
        self.assertEqual(invite.doc_type, Invite.DOC_TYPE)
        self.assertEqual(invite.doc_type, "invite")

    def test_token_generated_on_init(self):
        invite = Invite()
        self.assertIsNotNone(invite.token)
        self.assertGreater(len(invite.token), 10)

    def test_tokens_are_unique(self):
        tokens = {Invite().token for _ in range(50)}
        self.assertEqual(len(tokens), 50)

    def test_id_derives_from_token(self):
        invite = Invite()
        expected_id = f"invite::{invite.token}"
        self.assertEqual(invite.new_key(), expected_id)

    def test_status_constants(self):
        self.assertEqual(Invite.STATUS_PENDING, "pending")
        self.assertEqual(Invite.STATUS_ACCEPTED, "accepted")
        self.assertEqual(Invite.STATUS_EXPIRED, "expired")
        self.assertEqual(Invite.STATUS_CANCELLED, "cancelled")

    def test_status_stored_and_retrieved(self):
        invite = Invite()
        invite.status = Invite.STATUS_ACCEPTED
        self.assertEqual(invite.status, Invite.STATUS_ACCEPTED)

    def test_round_trip_from_dict(self):
        invite = Invite()
        invite.invitee_email = "user@example.com"
        invite.inviter_user_id = "user::abc"
        invite.status = Invite.STATUS_PENDING
        invite.sent_at = 1000.0
        invite.expiry_date = 2000.0

        restored = Invite(invite.as_dict())
        self.assertEqual(restored.invitee_email, "user@example.com")
        self.assertEqual(restored.inviter_user_id, "user::abc")
        self.assertEqual(restored.status, Invite.STATUS_PENDING)
        self.assertEqual(restored.sent_at, 1000.0)
        self.assertEqual(restored.expiry_date, 2000.0)


class TestInvitesValidate(TestDao):
    """Integration tests for invites_validate (requires CouchDB)."""

    @property
    def invites(self):
        return self.dao.invites

    def _make_invite(self, **kwargs) -> Invite:
        invite = Invite()
        invite.inviter_user_id = "user::test"
        invite.invitee_email = kwargs.get("invitee_email", "user@example.com")
        invite.status = kwargs.get("status", Invite.STATUS_PENDING)
        invite.sent_at = time.time()
        invite.expiry_date = kwargs.get("expiry_date", time.time() + 14 * 86400)
        self.assertTrue(self.invites.create(invite))
        return invite

    def test_validate_success(self):
        invite = self._make_invite(invitee_email="good@example.com")
        result = invites_validate(self.dao, invite.token, "good@example.com")
        self.assertEqual(result.token, invite.token)

    def test_validate_email_case_insensitive(self):
        invite = self._make_invite(invitee_email="Good@Example.COM")
        result = invites_validate(self.dao, invite.token, "good@example.com")
        self.assertEqual(result.token, invite.token)

    def test_validate_bad_token(self):
        with self.assertRaises(ActionError) as ctx:
            invites_validate(self.dao, "not-a-real-token", "user@example.com")
        self.assertEqual(ctx.exception.message, INVITE_INVALID_MESSAGE)

    def test_validate_email_mismatch(self):
        invite = self._make_invite(invitee_email="real@example.com")
        with self.assertRaises(ActionError) as ctx:
            invites_validate(self.dao, invite.token, "other@example.com")
        self.assertEqual(ctx.exception.message, INVITE_INVALID_MESSAGE)

    def test_validate_cancelled(self):
        invite = self._make_invite(status=Invite.STATUS_CANCELLED)
        with self.assertRaises(ActionError) as ctx:
            invites_validate(self.dao, invite.token, invite.invitee_email)
        self.assertEqual(ctx.exception.message, INVITE_INVALID_MESSAGE)

    def test_validate_expired_status(self):
        invite = self._make_invite(
            status=Invite.STATUS_EXPIRED,
            expiry_date=time.time() - 100,
        )
        with self.assertRaises(ActionError) as ctx:
            invites_validate(self.dao, invite.token, invite.invitee_email)
        self.assertEqual(ctx.exception.message, INVITE_INVALID_MESSAGE)

    def test_validate_pending_but_past_expiry_date(self):
        """Safety-net: pending status but expired date should be refused."""
        invite = self._make_invite(
            status=Invite.STATUS_PENDING,
            expiry_date=time.time() - 100,
        )
        with self.assertRaises(ActionError) as ctx:
            invites_validate(self.dao, invite.token, invite.invitee_email)
        self.assertEqual(ctx.exception.message, INVITE_INVALID_MESSAGE)
