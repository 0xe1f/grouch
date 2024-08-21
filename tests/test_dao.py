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

from dao import Connection
from dao import Database
import bcrypt
import entity
import tomllib
import unittest

class TestDao(unittest.TestCase):

    TEST_DB_NAME = "test__test"

    @classmethod
    def setUpClass(cls):
        cls._conn = Connection()

        with open("config.toml", "rb") as file:
            config = tomllib.load(file)

        cls._conn.connect(
            __class__.TEST_DB_NAME,
            config["DATABASE_USERNAME"],
            config["DATABASE_PASSWORD"],
            config["DATABASE_HOST"],
            config.get("DATABASE_PORT"),
        )
        cls._dao = Database(cls._conn.db)

    @classmethod
    def tearDownClass(cls):
        cls._conn.destroy()

    def setUp(self) -> None:
        self.users = self.__class__._dao.users

    def tearDown(self) -> None:
        # FIXME: delete all matching entities
        if user := self.users.find_by_username("username"):
            self.users.delete_by_id(user.id)

    def test_user_create(self):
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

        # Compare records - except revision
        user.rev = loaded_user.rev
        self.assertEqual(user, loaded_user)

    def test_user_find_by_username(self):
        # FIXME: inject some random users too
        user = entity.User()
        user.username = "username"
        user.email_address = "email"

        self.assertTrue(self.users.create(user))

        loaded_user = self.users.find_by_username(user.username)
        self.assertIsNotNone(loaded_user)
        self.assertEqual(loaded_user.username, user.username)

    def test_user_find_by_email_address(self):
        # FIXME: inject some random users too
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

if __name__ == '__main__':
    unittest.main()
