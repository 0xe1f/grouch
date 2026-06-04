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
from entity import Feed

FeedMeta = tuple[str, str]

class FeedDao(Dao):

    BY_URL = "maint/feeds_by_url"
    ALL_BY_UPDATED = "maint/feeds_all_by_updated"
    ALL_BY_TITLE = "maint/feeds_all_by_title"

    def find_by_id(
        self,
        *feed_ids: str,
    ) -> list[Feed]:
        matches = []
        for item in self.db.view(self.__class__.ALL_DOCS, keys=feed_ids, include_docs=True):
            matches.append(Feed(item.doc))

        return matches

    def map_metadata_by_url(
        self,
        *urls: str,
    ) -> dict[str, FeedMeta]:
        matches = {}
        for item in self.db.view(self.__class__.BY_URL, keys = urls):
            matches[item.key] = (item.id, item.value)

        return matches

    def iter_updated_before(
        self,
        stale_start: str=int,
    ):
        batch_limit = 40
        options = {
            "descending": True,
            "include_docs": True,
        }
        if stale_start:
            options.update(startkey=stale_start)

        iterable = self.db.iterview("maint/updated_feeds", batch_limit, **options)
        for item in iterable:
            yield Feed(item.doc)

    def get_page_by_updated(
        self,
        start: dict|None=None,
        limit: int=40,
    ) -> tuple[list[Feed], dict|None]:
        return self._get_page(self.__class__.ALL_BY_UPDATED, start, limit)

    def get_page_by_title(
        self,
        start: dict|None=None,
        limit: int=40,
    ) -> tuple[list[Feed], dict|None]:
        return self._get_page(self.__class__.ALL_BY_TITLE, start, limit)

    def _get_page(
        self,
        view: str,
        start: dict|None,
        limit: int,
    ) -> tuple[list[Feed], dict|None]:
        options = {
            "include_docs": True,
            "limit": limit + 1,
        }
        if start:
            options["startkey"] = start["key"]
            options["startkey_docid"] = start["id"]

        rows = list(self.db.view(view, **options))
        next_start = None
        if len(rows) > limit:
            extra = rows[limit]
            next_start = {"key": extra.key, "id": extra.id}
            rows = rows[:limit]

        return [Feed(row.doc) for row in rows], next_start

    def set_disabled(
        self,
        feed_ids: list[str],
        disabled: bool,
    ):
        feeds = self.find_by_id(*feed_ids)
        with self.new_q() as q:
            for feed in feeds:
                feed.disabled = disabled
                q.enqueue(feed)
