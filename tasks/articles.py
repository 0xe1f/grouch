from store import generate_articles_by_sub
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

    logging.info(f"Moved {bulk_q.written_count} articles belonging to {sub_id} ({time() - start_time:.2}s)")
