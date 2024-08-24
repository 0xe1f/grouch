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
import bcrypt
import entity
import random

class TestDaoUsers(TestDao):

    @property
    def users(self):
        return self.dao.users

    def test_user_create(self):
        self._create_random_users(random.randrange(3, 8))

        user = entity.User()
        user.username = "username"
        user.email_address = "email"
        user.set_hashed_password("password", bcrypt.gensalt())

        # Random field checks
        self.assertTrue(user.hashed_password)
        self.assertNotEqual(user.hashed_password, "password")
        self.assertTrue(user.uid)
        self.assertNotEqual(user.uid, user.username)

        # Ensure user created
        self.assertTrue(self.users.create(user))

        # Ensure user is loaded
        loaded_user = self.users.find_by_id(user.id)
        self.assertIsNotNone(loaded_user)
        self.assertEqual(user, loaded_user)

    def test_user_find_by_username(self):
        self._create_random_users(random.randrange(3, 8))

        user = entity.User()
        user.username = "username"
        user.email_address = "email"

        self.assertTrue(self.users.create(user))

        loaded_user = self.users.find_by_username(user.username)
        self.assertIsNotNone(loaded_user)
        self.assertEqual(loaded_user.username, user.username)

    def test_user_find_by_email_address(self):
        self._create_random_users(random.randrange(3, 8))

        user = entity.User()
        user.username = "username"
        user.email_address = "email"

        self.assertTrue(self.users.create(user))

        loaded_user = self.users.find_by_email_address(user.email_address)
        self.assertIsNotNone(loaded_user)
        self.assertEqual(loaded_user.email_address, user.email_address)

    def test_user_dedupe_id(self):
        user = entity.User()
        user.username = "username"
        user.email_address = "email"

        # Ensure user created
        self.assertTrue(self.users.create(user))

        # Ensure user creation fails second time
        self.assertFalse(self.users.create(user))

    def test_user_dedupe_username(self):
        user = entity.User()
        user.username = "username"
        user.email_address = "email"

        # Ensure user created
        self.assertTrue(self.users.create(user))

        # Change uid (affects id) and email address
        user.uid = "something else"
        user.email_address = "another email"

        # Ensure user creation fails second time
        self.assertFalse(self.users.create(user))
        self.assertIsNone(self.users.find_by_email_address(user.email_address))

    def test_user_dedupe_email_address(self):
        user = entity.User()
        user.username = "username"
        user.email_address = "email"

        # Ensure user created
        self.assertTrue(self.users.create(user))

        # Change uid (affects id) and username
        user.uid = "something else"
        user.username = "another username"

        # Ensure user creation fails second time
        self.assertFalse(self.users.create(user))
        self.assertIsNone(self.users.find_by_username(user.username))

    def _create_random_users(self, count: int=1):
        with self.users.new_q() as bulk_q:
            for _ in range(count):
                user = entity.User()
                user.username = self.random_string()
                user.email_address = self.random_string()

                bulk_q.enqueue(user)

        self.assertEqual(bulk_q.written_count, count)
