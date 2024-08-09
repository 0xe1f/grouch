from common import build_key
from common import now_in_iso
from datatype import Article
from store.bulk_update_queue import BulkUpdateQueue
from store.connection import Connection

type ArticlePageMarker = tuple
type ArticlePage = tuple[list[Article], ArticlePageMarker|None]

def find_articles_by_id(conn: Connection, *article_ids: str) -> list[Article]:
    matches = []
    for item in conn.db.view("_all_docs", keys=article_ids, include_docs=True):
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
    for item in conn.db.view("maint/articles_by_user", **options):
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

    for item in conn.db.view("maint/articles_by_prop", **options):
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
    view_name = "maint/articles_by_sub_unread" if unread_only else "maint/articles_by_sub"

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
    for item in conn.db.view("_all_docs", **options):
        doc = item.get("doc")
        if doc:
            yield Article(doc)

def enqueue_articles(bulk_q: BulkUpdateQueue, *articles: Article):
    for article in articles:
        if not article.id:
            article.id = article.build_key()
        article.updated = now_in_iso()
        bulk_q.enqueue_tuple((article.doc(), article))
