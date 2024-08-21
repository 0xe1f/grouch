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

from .articles import ArticleDao
from .bulk_update_queue import BulkUpdateQueue
from .entries import EntryDao
from .feeds import FeedDao
from .folders import FolderDao
from .subscriptions import SubscriptionDao
from .users import UserDao
import couchdb.client as couchdb

class Database:

    def __init__(self, db: couchdb.Database):
        self._articles = ArticleDao(db)
        self._entries = EntryDao(db)
        self._feeds = FeedDao(db)
        self._folders = FolderDao(db)
        self._subs = SubscriptionDao(db)
        self._users = UserDao(db)

    @property
    def articles(self) -> ArticleDao:
        return self._articles

    @property
    def entries(self) -> EntryDao:
        return self._entries

    @property
    def feeds(self) -> FeedDao:
        return self._feeds

    @property
    def folders(self) -> FolderDao:
        return self._folders

    @property
    def subs(self) -> SubscriptionDao:
        return self._subs

    @property
    def users(self) -> UserDao:
        return self._users

    def new_q(self, track_ids: bool=False) -> BulkUpdateQueue:
        return BulkUpdateQueue(self._db, track_ids=track_ids)
