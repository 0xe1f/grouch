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

from common import format_iso
from datatype import FeedContent
from store import views
from store.connection import Connection
from time import struct_time

def find_feeds_by_id(conn: Connection, *feed_ids: str) -> list[FeedContent]:
    matches = []
    for item in conn.db.view(views.ALL_DOCS, keys=feed_ids, include_docs=True):
        matches.append(FeedContent(item.doc))

    return matches

def find_feed_ids_by_url(conn: Connection, *urls: str) -> dict:
    matches = {}
    for item in conn.db.view(views.FEEDS_BY_URL, keys = urls):
        matches[item.key] = item.id

    return matches

def stale_feeds(conn: Connection, stale_start: struct_time=None):
    batch_limit = 40
    options = {
        "descending": True,
        "include_docs": True,
    }
    if stale_start:
        options.update(startkey=format_iso(stale_start))

    iterable = conn.db.iterview("maint/updated_feeds", batch_limit, **options)
    for item in iterable:
        yield FeedContent(item.doc)
