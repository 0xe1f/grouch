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
from common import first_or_none
from couchdb.http import ResourceConflict
from entity import User
from datetime import datetime
import logging

class UserDao(Dao):

    BY_EMAIL = "maint/users_by_email"
    BY_USERNAME = "maint/users_by_username"

    def find_by_id(
        self,
        user_id: str,
    ) -> User:
        for item in self.db.view(self.__class__.ALL_DOCS, key=user_id, include_docs=True):
            return User(item.doc)

        return None

    def find_by_username(
        self,
        username: str,
    ) -> User:
        for item in self.db.view(self.__class__.BY_USERNAME, key=username, include_docs=True, reduce=False):
            if item.doc:
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
        elif self._entity_count(self.__class__.BY_USERNAME, user.email_address) > 0:
            logging.error(f"User with email address {user.email_address} already exists")
            return False
        elif self._entity_count(self.__class__.BY_EMAIL, user.email_address) > 0:
            logging.error(f"User with email address {user.email_address} already exists")
            return False

        user.created = datetime.now().timestamp()
        user.updated = user.created

        try:
            new_id, _ = self.db.save(user.as_dict())
        except ResourceConflict as e:
            logging.exception(f"Error writing user {user.id}", e)
            return False

        # Ensure we didn't end up writing multiple addresses
        is_email_dupe = self._entity_count(self.__class__.BY_EMAIL, user.email_address) > 1
        is_username_dupe = self._entity_count(self.__class__.BY_USERNAME, user.username) > 1

        if is_email_dupe or is_username_dupe:
            if is_email_dupe:
                logging.warning(f"Existing user with email ({user.email_address})")
            elif is_username_dupe:
                logging.warning(f"Existing user with username ({user.username})")
            # Delete dupe account
            del self.db[new_id]
            return False

        return True

    def _entity_count(
        self,
        view_name: str,
        key: str,
    ) -> bool:
        result = self.db.view(view_name, limit=1)
        if next_item := first_or_none(result[key]):
            return next_item.value
        else:
            return 0
