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

from .bulk_update_queue import BulkUpdateQueue
from .dao import Dao
from common import first_index
from entity import Article
from entity import Entity

type ArticlePageMarker = tuple
type ArticlePage = tuple[list[Article], ArticlePageMarker|None]

class ArticleDao(Dao):

    BY_FOLDER = "maint/articles_by_folder"
    BY_FOLDER_UNREAD = "maint/articles_by_folder_unread"
    BY_PROP = "maint/articles_by_prop"
    BY_SUB = "maint/articles_by_sub"
    BY_SUB_UNREAD = "maint/articles_by_sub_unread"
    BY_TAG = "maint/articles_by_tag"
    BY_USER = "maint/articles_by_user"
    BY_USER_BY_TAG = "maint/tags_by_user"

    def find_by_id(
        self,
        *article_ids: str,
    ) -> list[Article]:
        matches = []
        for item in self.db.view(self.__class__.ALL_DOCS, keys=article_ids, include_docs=True):
            if "doc" in item:
                matches.append(Article(item.doc))

        return matches

    def find_tags_by_user(
        self,
        user_id: str,
        limit: int=40,
    ):
        options = {
            "start_key": [user_id],
            "end_key": [user_id, {}],
            "reduce": True,
            "group": True,
        }
        matches = []
        for item in self.db.view(self.__class__.BY_USER_BY_TAG, **options):
            if item.key and len(item.key) >= 2:
                matches.append(item.key[1])
            if len(matches) >= limit:
                break

        return matches

    def get_page_by_user(
        self,
        user_id: str,
        start: str=None,
        limit: int=40,
    ) -> ArticlePage:
        options = {
            "end_key": [user_id],
            "start_key": start if start else [user_id, {}],
            "include_docs": True,
            "limit": limit + 1,
            "descending": True,
        }

        next_start = None
        matches = []
        for item in self.db.view(self.__class__.BY_USER, **options):
            if len(matches) < limit:
                matches.append(Article(item.doc))
            else:
                next_start = item.key
                break

        return matches, next_start

    def get_page_by_prop(
        self,
        user_id: str,
        prop: str,
        start: str=None,
        limit: int=40,
    ) -> ArticlePage:
        options = {
            "end_key": [user_id, prop],
            "start_key": start if start else [user_id, prop, {}],
            "include_docs": True,
            "limit": limit + 1,
            "descending": True,
        }

        next_start = None
        matches = []

        for item in self.db.view(self.__class__.BY_PROP, **options):
            if len(matches) < limit:
                matches.append(Article(item.doc))
            else:
                next_start = item.key
                break

        return matches, next_start

    def get_page_by_tag(
        self,
        user_id: str,
        tag: str,
        start: str=None,
        limit: int=40,
    ) -> ArticlePage:
        options = {
            "end_key": [ user_id, tag ],
            "start_key": start if start else [ user_id, tag, {} ],
            "include_docs": True,
            "limit": limit + 1,
            "descending": True,
        }

        next_start = None
        matches = []

        for item in self.db.view(self.__class__.BY_TAG, **options):
            if len(matches) < limit:
                matches.append(Article(item.doc))
            else:
                next_start = item.key
                break

        return matches, next_start

    def get_page_by_sub(
        self,
        sub_id: str,
        start: str=None,
        unread_only: bool=False,
        limit: int=40,
    ) -> ArticlePage:
        options = {
            "end_key": [sub_id],
            "start_key": start if start else [sub_id, {}],
            "include_docs": True,
            "limit": limit + 1,
            "descending": True,
        }

        next_start = None
        matches = []
        view_name = self.__class__.BY_SUB_UNREAD if unread_only else self.__class__.BY_SUB

        for item in self.db.view(view_name, **options):
            if len(matches) < limit:
                matches.append(Article(item.doc))
            else:
                next_start = item.key
                break

        return matches, next_start

    def get_page_by_folder(
        self,
        folder_id: str,
        start: str=None,
        unread_only: bool=False,
        limit: int=40,
    ) -> ArticlePage:
        options = {
            "end_key": [folder_id],
            "start_key": start if start else [folder_id, {}],
            "descending": True,
            "include_docs": True,
            "limit": limit + 1,
        }

        next_start = None
        matches = []
        view_name = self.__class__.BY_FOLDER_UNREAD if unread_only else self.__class__.BY_FOLDER

        for item in self.db.view(view_name, **options):
            if len(matches) < limit:
                matches.append(Article(item.doc))
            else:
                next_start = item.key
                break

        return matches, next_start

    def iter_by_user_by_entry(
        self,
        user_id: str,
        *entry_ids: str,
    ):
        options = {
            "include_docs": True,
            "keys": [Entity.build_key("article", user_id, entry_id) for entry_id in entry_ids],
        }
        for item in self.db.view(self.__class__.ALL_DOCS, **options):
            doc = item.get("doc")
            if doc:
                yield Article(doc)

    def iter_by_sub(
        self,
        sub_id: str,
        unread_only: bool=False,
        batch_size: int=40,
    ):
        options = {
            "end_key": [sub_id],
            "start_key":[sub_id, {}],
            "descending": True,
            "include_docs": True,
        }
        if unread_only:
            view = self.__class__.BY_SUB_UNREAD
        else:
            view = self.__class__.BY_SUB
        for item in self.db.iterview(view, batch_size, **options):
            yield Article(item.doc)

    def iter_by_folder(
        self,
        folder_id: str,
        unread_only: bool=False,
        batch_size: int=40,
    ):
        options = {
            "end_key": [folder_id],
            "start_key":[folder_id, {}],
            "descending": True,
            "include_docs": True,
        }
        if unread_only:
            view = self.__class__.BY_FOLDER_UNREAD
        else:
            view = self.__class__.BY_FOLDER
        for item in self.db.iterview(view, batch_size, **options):
            yield Article(item.doc)

    def iter_by_user(
        self,
        user_id: str,
        unread_only: bool=False,
        batch_size: int=40,
    ):
        options = {
            "descending": True,
            "include_docs": True,
        }
        if unread_only:
            view = self.__class__.BY_PROP
            options = options | {
                "end_key": [user_id, Article.PROP_UNREAD],
                "start_key":[user_id, Article.PROP_UNREAD, {}],
            }
        else:
            view = self.__class__.BY_USER
            options = options | {
                "end_key": [user_id],
                "start_key":[user_id, {}],
            }
        for item in self.db.iterview(view, batch_size, **options):
            yield Article(item.doc)

    def iter_by_user_by_tag(
        self,
        user_id: str,
        tag: str,
        batch_size: int=40,
    ):
        options = {
            "start_key": [user_id, tag],
            "end_key": [[user_id, tag], {}],
            "include_docs": True,
        }
        for item in self.db.iterview(self.__class__.BY_TAG, batch_size, **options):
            yield Article(item.doc)

    def move_by_sub(
        self,
        bulk_q: BulkUpdateQueue,
        sub_id: str,
        dest_folder_id: str|None,
    ) -> int:
        enqueued_count = bulk_q.enqueued_count

        for article in self.iter_by_sub(sub_id):
            article.folder_id = dest_folder_id
            bulk_q.enqueue(article)

        return bulk_q.enqueued_count - enqueued_count

    def remove_all_tags_by_user_by_name(
        self,
        bulk_q: BulkUpdateQueue,
        user_id: str,
        tag: str,
    ) -> int:
        enqueued_count = bulk_q.enqueued_count

        for article in self.iter_by_user_by_tag(user_id, tag):
            index = first_index(article.tags, tag)
            if index > -1:
                del article.tags[index]
                bulk_q.enqueue(article)

        return bulk_q.enqueued_count - enqueued_count

    def mark_as_read_by_sub(
        self,
        bulk_q: BulkUpdateQueue,
        sub_id: str,
    ) -> int:
        enqueued_count = bulk_q.enqueued_count
        for article in self.iter_by_sub(sub_id, unread_only=True):
            article.toggle_prop(Article.PROP_UNREAD, False)
            bulk_q.enqueue(article)

        return bulk_q.enqueued_count - enqueued_count

    def mark_as_read_by_folder(
        self,
        bulk_q: BulkUpdateQueue,
        folder_id: str,
    ) -> int:
        enqueued_count = bulk_q.enqueued_count

        for article in self.iter_by_folder(folder_id, unread_only=True):
            article.toggle_prop(Article.PROP_UNREAD, False)
            bulk_q.enqueue(article)

        return bulk_q.enqueued_count - enqueued_count

    def mark_as_read_by_user(
        self,
        bulk_q: BulkUpdateQueue,
        user_id: str,
    ) -> int:
        enqueued_count = bulk_q.enqueued_count

        for article in self.iter_by_user(user_id, unread_only=True):
            article.toggle_prop(Article.PROP_UNREAD, False)
            bulk_q.enqueue(article)

        return bulk_q.enqueued_count - enqueued_count

    def delete_by_sub(
        self,
        bulk_q: BulkUpdateQueue,
        sub_id: str,
    ) -> int:
        enqueued_count = bulk_q.enqueued_count

        for article in self.iter_by_sub(sub_id):
            article.mark_deleted()
            bulk_q.enqueue(article)

        return bulk_q.enqueued_count - enqueued_count
