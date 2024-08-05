from common import build_key
from common import now_in_iso
from datatype import Article
from store.bulk_update_queue import BulkUpdateQueue
from store.connection import Connection

def find_articles_by_user(conn: Connection, user_id: str, limit: int=40) -> list[Article]:
    matches = []
    for item in conn.db.view("maint/articles-by-user", end_key=[ user_id ], start_key=[ user_id, {}], include_docs=True, limit=limit, descending=True):
        matches.append(Article(item["doc"]))
    return matches

def find_articles_by_sub(conn: Connection, sub_id: str, limit: int=40) -> list[Article]:
    matches = []
    for item in conn.db.view("maint/articles-by-sub", end_key=[ sub_id ], start_key=[ sub_id, {}], include_docs=True, limit=limit, descending=True):
        matches.append(Article(item["doc"]))
    return matches

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
