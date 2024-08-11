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
from datatype import Article
from store import views
from store.connection import Connection

type ArticlePageMarker = tuple
type ArticlePage = tuple[list[Article], ArticlePageMarker|None]

def find_articles_by_id(conn: Connection, *article_ids: str) -> list[Article]:
    matches = []
    for item in conn.db.view(views.ALL_DOCS, keys=article_ids, include_docs=True):
        if "doc" in item:
            matches.append(Article(item["doc"]))

    return matches

def find_articles_by_user(conn: Connection, user_id: str, start: str=None, limit: int=40) -> ArticlePage:
    options = {
        "end_key": [user_id],
        "start_key": start if start else [user_id, {}],
        "include_docs": True,
        "limit": limit + 1,
        "descending": True,
    }

    next_start = None
    matches = []
    for item in conn.db.view(views.ARTICLES_BY_USER, **options):
        if len(matches) < limit:
            matches.append(Article(item.doc))
        else:
            next_start = item.key
            break

    return matches, next_start

def find_articles_by_prop(conn: Connection, user_id: str, prop: str, start: str=None, limit: int=40) -> ArticlePage:
    options = {
        "end_key": [user_id, prop],
        "start_key": start if start else [user_id, prop, {}],
        "include_docs": True,
        "limit": limit + 1,
        "descending": True,
    }

    next_start = None
    matches = []

    for item in conn.db.view(views.ARTICLES_BY_PROP, **options):
        if len(matches) < limit:
            matches.append(Article(item.doc))
        else:
            next_start = item.key
            break

    return matches, next_start

def find_articles_by_tag(conn: Connection, user_id: str, tag: str, start: str=None, limit: int=40) -> ArticlePage:
    options = {
        "end_key": [user_id, tag],
        "start_key": start if start else [user_id, tag, {}],
        "include_docs": True,
        "limit": limit + 1,
        "descending": True,
    }

    next_start = None
    matches = []

    for item in conn.db.view(views.ARTICLES_BY_TAG, **options):
        if len(matches) < limit:
            matches.append(Article(item.doc))
        else:
            next_start = item.key
            break

    return matches, next_start

def find_articles_by_sub(conn: Connection, sub_id: str, start: str=None, unread_only: bool=False, limit: int=40) -> ArticlePage:
    options = {
        "end_key": [sub_id],
        "start_key": start if start else [sub_id, {}],
        "include_docs": True,
        "limit": limit + 1,
        "descending": True,
    }

    next_start = None
    matches = []
    view_name = views.ARTICLES_BY_SUB_UNREAD if unread_only else views.ARTICLES_BY_SUB

    for item in conn.db.view(view_name, **options):
        if len(matches) < limit:
            matches.append(Article(item.doc))
        else:
            next_start = item.key
            break

    return matches, next_start

def find_articles_by_entry(conn: Connection, user_id: str, *entry_ids: str):
    options = {
        "include_docs": True,
        "keys": [build_key("article", user_id, entry_id) for entry_id in entry_ids],
    }
    for item in conn.db.view(views.ALL_DOCS, **options):
        doc = item.get("doc")
        if doc:
            yield Article(doc)

def find_articles_by_folder(conn: Connection, sub_id: str, start: str=None, unread_only: bool=False, limit: int=40) -> ArticlePage:
    options = {
        "end_key": [sub_id],
        "start_key": start if start else [sub_id, {}],
        "descending": True,
        "include_docs": True,
        "limit": limit + 1,
    }

    next_start = None
    matches = []
    view_name = views.ARTICLES_BY_FOLDER_UNREAD if unread_only else views.ARTICLES_BY_FOLDER

    for item in conn.db.view(view_name, **options):
        if len(matches) < limit:
            matches.append(Article(item.doc))
        else:
            next_start = item.key
            break

    return matches, next_start

def generate_articles_by_sub(conn: Connection, sub_id: str, unread_only: bool=False, batch_size: int=40):
    options = {
        "end_key": [sub_id],
        "start_key":[sub_id, {}],
        "descending": True,
        "include_docs": True,
    }
    if unread_only:
        view = views.ARTICLES_BY_SUB_UNREAD
    else:
        view = views.ARTICLES_BY_SUB
    for item in conn.db.iterview(view, batch_size, **options):
        yield Article(item.doc)

def generate_articles_by_folder(conn: Connection, folder_id: str, unread_only: bool=False, batch_size: int=40):
    options = {
        "end_key": [folder_id],
        "start_key":[folder_id, {}],
        "descending": True,
        "include_docs": True,
    }
    if unread_only:
        view = views.ARTICLES_BY_FOLDER_UNREAD
    else:
        view = views.ARTICLES_BY_FOLDER
    for item in conn.db.iterview(view, batch_size, **options):
        yield Article(item.doc)

def generate_articles_by_user(conn: Connection, user_id: str, unread_only: bool=False, batch_size: int=40):
    options = {
        "descending": True,
        "include_docs": True,
    }
    if unread_only:
        view = views.ARTICLES_BY_PROP
        options = options | {
            "end_key": [user_id, Article.PROP_UNREAD],
            "start_key":[user_id, Article.PROP_UNREAD, {}],
        }
    else:
        view = views.ARTICLES_BY_USER
        options = options | {
            "end_key": [user_id],
            "start_key":[user_id, {}],
        }
    for item in conn.db.iterview(view, batch_size, **options):
        yield Article(item.doc)

def generate_articles_by_tag(conn: Connection, user_id: str, tag: str, batch_size: int=40):
    options = {
        "start_key": [user_id, tag],
        "end_key": [[user_id, tag], {}],
        "include_docs": True,
    }
    for item in conn.db.iterview(views.ARTICLES_BY_TAG, batch_size, **options):
        yield Article(item.doc)
