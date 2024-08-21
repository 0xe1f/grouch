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
from datatype import FeedContent

FeedMeta = tuple[str, str]

class FeedDao(Dao):

    BY_URL = "maint/feeds_by_url"

    def find_by_id(
        self,
        *feed_ids: str,
    ) -> list[FeedContent]:
        matches = []
        for item in self.db.view(self.__class__.ALL_DOCS, keys=feed_ids, include_docs=True):
            matches.append(FeedContent(item.doc))

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
            yield FeedContent(item.doc)
