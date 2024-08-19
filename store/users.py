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
from couchdb.http import ResourceConflict
from datatype import User
from datetime import datetime
from store.connection import Connection
from store import views
import logging

def find_user_by_username(conn: Connection, username: str) -> User:
    for item in conn.db.view(views.USERS_BY_USERNAME, key=username, include_docs=True):
        return User(item.doc)

    return None

def find_user_id(conn: Connection, username: str) -> str:
    item_id = build_key("user", username)
    if conn.db.get(item_id):
        return item_id

    return None

def fetch_user(conn: Connection, user_id: str) -> User:
    for item in conn.db.view(views.ALL_DOCS, key=user_id, include_docs=True):
        return User(item.doc)

    return None

def create_user(conn: Connection, user: User) -> bool:
    if not user.id:
        user.id = user.new_key()
    if user.id in conn.db:
        logging.error(f"User with id {user.id} already exists")
        return False
    elif _email_address_count(conn, user.email_address) > 0:
        logging.error(f"User with email address {user.email_address} already exists")
        return False

    user.created = datetime.now().timestamp()
    user.updated = user.created

    try:
        new_id, _ = conn.db.save(user.as_dict())
    except ResourceConflict as e:
        logging.exception(f"Error writing user {user.id}", e)
        return False

    # Ensure we didn't end up writing multiple addresses
    new_count = _email_address_count(conn, user.email_address)
    if new_count > 1:
        logging.warning(f"There are {new_count} instances of users with address {user.email_address}")
        # Delete dupe account
        del conn.db[new_id]
        return False

    return True

def _email_address_count(conn: Connection, email_address: str) -> bool:
    result = conn.db.view(views.USERS_BY_EMAIL, reduce=True, group=True, limit=1)
    next_item = next(result[email_address].__iter__(), None)

    if next_item:
        return next_item.value
    else:
        return 0
