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
from couchdb.http import ResourceConflict
from entity import User
from datetime import datetime
import logging

class UserDao(Dao):

    BY_EMAIL = "maint/users_by_email"
    BY_USERNAME = "maint/users_by_username"

    def find_by_username(
        self,
        username: str,
    ) -> User:
        for item in self.db.view(self.__class__.BY_USERNAME, key=username, include_docs=True):
            if item.doc:
                return User(item.doc)

        return None

    def find_by_id(
        self,
        user_id: str,
    ) -> User:
        for item in self.db.view(self.__class__.ALL_DOCS, key=user_id, include_docs=True):
            return User(item.doc)

        return None

    def create(
        self,
        user: User,
    ) -> bool:
        if not user.id:
            user.id = user.new_key()
        if user.id in self.db:
            logging.error(f"User with id {user.id} already exists")
            return False
        elif self._email_address_count(user.email_address) > 0:
            logging.error(f"User with email address {user.email_address} already exists")
            return False

        # FIXME: unique username
        # FIXME: user id is not username
        user.created = datetime.now().timestamp()
        user.updated = user.created

        try:
            new_id, _ = self.db.save(user.as_dict())
        except ResourceConflict as e:
            logging.exception(f"Error writing user {user.id}", e)
            return False

        # Ensure we didn't end up writing multiple addresses
        new_count = self._email_address_count(user.email_address)
        if new_count > 1:
            logging.warning(f"There are {new_count} instances of users with address {user.email_address}")
            # Delete dupe account
            del self.db[new_id]
            return False

        return True

    def _email_address_count(
        self,
        email_address: str,
    ) -> bool:
        result = self.db.view(self.__class__.BY_EMAIL, reduce=True, group=True, limit=1)
        if next_item := next(result[email_address].__iter__(), None):
            return next_item.value
        else:
            return 0
