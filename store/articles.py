from common import build_key
from common import now_in_iso
from datatype import Article
from store.bulk_update_queue import BulkUpdateQueue
from store.connection import Connection

def find_articles_by_user(conn: Connection, user_id: str, limit: int=40) -> list[Article]:
    matches = []
    for item in conn.db.view("maint/articles-by-user", start_key=[ user_id ], end_key=[ user_id, {}], include_docs=True, limit=limit):
        matches.append(Article(item["doc"]["content"]))
    return matches

def find_articles_by_sub(conn: Connection, sub_id: str, limit: int=40) -> list[Article]:
    matches = []
    for item in conn.db.view("maint/articles-by-sub", start_key=[ sub_id ], end_key=[ sub_id, {}], include_docs=True, limit=limit):
        matches.append(Article(item["doc"]["content"]))
    return matches

def find_articles_by_entry(conn: Connection, user_id: str, *entry_ids: str):
    options = {
        "include_docs": True,
        "keys": [build_key("article", user_id, entry_id) for entry_id in entry_ids],
    }
    for item in conn.db.view("_all_docs", **options):
        doc = item.get("doc")
        if doc:
            yield Article(doc["content"]), doc["_rev"]

def enqueue_articles(bulk_q: BulkUpdateQueue, *articles: tuple[Article, str]):
    for article, rev in articles:
        if not article.id:
            article.id = build_key("article", article.user_id, article.entry_id)
        doc = {
            "_id": article.id,
            "doc_type": "article",
            "content": article.doc(),
            "updated": now_in_iso(),
        }
        if rev:
            doc["_rev"] = rev
        bulk_q.enqueue_tuple((doc, article))
