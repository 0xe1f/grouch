from common import first_index
from store import generate_articles_by_sub
from store import generate_articles_by_tag
from store import BulkUpdateQueue
from store import Connection
from time import time
import logging

def move_articles(conn: Connection, sub_id: str, dest_folder_id: str|None):
    start_time = time()
    logging.info(f"Moving {sub_id} to {dest_folder_id}")

    with BulkUpdateQueue(conn, track_ids=False) as bulk_q:
        for article in generate_articles_by_sub(conn, sub_id):
            article.folder_id = dest_folder_id
            bulk_q.enqueue_flex(article)

    logging.info(f"Moved {bulk_q.written_count} articles ({time() - start_time:.2}s)")

def remove_tag_from_articles(conn: Connection, user_id: str, tag: str):
    start_time = time()
    logging.info(f"Removing '{tag}' from articles of {user_id}")

    with BulkUpdateQueue(conn, track_ids=False) as bulk_q:
        for article in generate_articles_by_tag(conn, user_id, tag):
            index = first_index(article.tags, tag)
            if index > -1:
                del article.tags[index]
                bulk_q.enqueue_flex(article)

    logging.info(f"Removed tag from {bulk_q.written_count} articles ({time() - start_time:.2}s)")
