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
import entity

class TestDaoArticles(TestDao):

    @property
    def articles(self):
        return self.dao.articles

    def test_articles_by_user(self):

        def override(_, article):
            article.user_id = "abc"

        def fetch_page(start, max):
            return self.dao.articles.get_page_by_user("abc", start, limit=max)

        self.assert_page(override, fetch_page)

    def test_articles_by_sub(self):

        def override(_, article):
            article.subscription_id = "abc"

        def fetch_page(start, max):
            return self.dao.articles.get_page_by_sub("abc", start, limit=max)

        self.assert_page(override, fetch_page)

    def test_articles_by_sub_unread(self):

        def override(i, article):
            article.subscription_id = "abc"
            article.props = [ entity.Article.PROP_UNREAD ] if i % 2 == 0 else []

        def fetch_page(start, max):
            return self.dao.articles.get_page_by_sub("abc", start, unread_only=True, limit=max)

        # Expect only half the items
        self.assert_page(override, fetch_page, 0.5)

    def test_articles_by_folder(self):

        def override(_, article):
            article.folder_id = "abc"

        def fetch_page(start, max):
            return self.dao.articles.get_page_by_folder("abc", start, limit=max)

        self.assert_page(override, fetch_page)

    def test_articles_by_folder_unread(self):

        def override(i, article):
            article.folder_id = "abc"
            article.props = [ entity.Article.PROP_UNREAD ] if i % 2 == 0 else []

        def fetch_page(start, max):
            return self.dao.articles.get_page_by_folder("abc", start, unread_only=True, limit=max)

        # Expect only half the items
        self.assert_page(override, fetch_page, 0.5)

    def test_articles_by_tag(self):

        def override(_, article):
            article.user_id = "abc"
            article.tags = [ "def", "123" ]

        def fetch_page(start, max):
            return self.dao.articles.get_page_by_tag("abc", "def", start, limit=max)

        self.assert_page(override, fetch_page)

    def test_articles_by_prop(self):

        def override(_, article):
            article.user_id = "abc"
            article.props = [ "star" ]

        def fetch_page(start, max):
            return self.dao.articles.get_page_by_prop("abc", "star", start, limit=max)

        self.assert_page(override, fetch_page)

    def assert_page(self, override, fetch_page, item_ratio=1):
        max_items = 40
        max_per_page = 5

        self._create_random_articles(max_items, override)

        item_count = 0
        page_count = 0
        next = None
        prev_sort_cols = None

        while True:
            (items, next) = fetch_page(next, max_per_page)
            # Assert items per page
            self.assertLessEqual(len(items), max_per_page)

            if items:
                page_count+=1
                for item in items:
                    item_count+=1
                    sort_cols = (item.published, item.updated)
                    if prev_sort_cols:
                        # Assert sort order across pages
                        self.assertGreaterEqual(prev_sort_cols, sort_cols)
                    prev_sort_cols = sort_cols
            if not next:
                break

        # Assert item count
        self.assertEqual(item_count, max_items * item_ratio)
        # Assert page count
        self.assertEqual(page_count, (max_items * item_ratio) // max_per_page)

    def _create_random_articles(self, count: int=1, setter=None) -> list[entity.Article]:
        items = []
        with self.articles.new_q() as bulk_q:
            for i in range(count):
                article = entity.Article()
                article.user_id = self.random_string()
                article.subscription_id = self.random_string()
                article.entry_id = self.random_string()
                article.synced = self.random_timestamp(jitter=172800)
                article.published = self.random_timestamp(jitter=172800)
                article.updated = self.random_timestamp(jitter=172800)
                if setter:
                    setter(i, article)

                items.append(article)
                bulk_q.enqueue(article)

        return items
