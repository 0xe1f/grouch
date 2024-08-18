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

from common import first_index
from datatype import Article
from store import generate_articles_by_folder
from store import generate_articles_by_sub
from store import generate_articles_by_tag
from store import generate_articles_by_user
from store import BulkUpdateQueue
from store import Connection
from time import time
import logging

def move_articles(conn: Connection, sub_id: str, dest_folder_id: str|None):
    start_time = time()
    logging.debug(f"Moving {sub_id} to {dest_folder_id}")

    with BulkUpdateQueue(conn, track_ids=False) as bulk_q:
        for article in generate_articles_by_sub(conn, sub_id):
            article.folder_id = dest_folder_id
            bulk_q.enqueue_flex(article)

    logging.info(f"Moved {bulk_q.written_count} articles ({time() - start_time:.2}s)")

def remove_tag_from_articles(conn: Connection, user_id: str, tag: str):
    start_time = time()
    logging.debug(f"Removing '{tag}' from articles of {user_id}")

    with BulkUpdateQueue(conn, track_ids=False) as bulk_q:
        for article in generate_articles_by_tag(conn, user_id, tag):
            index = first_index(article.tags, tag)
            if index > -1:
                del article.tags[index]
                bulk_q.enqueue_flex(article)

    logging.info(f"Removed tag from {bulk_q.written_count} articles ({time() - start_time:.2}s)")

# ---

def remove_articles_by_sub(bulk_q: BulkUpdateQueue, sub_id: str) -> bool:
    pending_count = bulk_q.pending_count
    written_count = bulk_q.written_count
    enqueued_count = bulk_q.enqueued_count

    for article in generate_articles_by_sub(bulk_q.connection, sub_id):
        article.mark_deleted()
        bulk_q.enqueue_flex(article)
    bulk_q.flush()

    written_count = bulk_q.written_count - written_count - pending_count
    enqueued_count = bulk_q.enqueued_count - enqueued_count

    return written_count == enqueued_count

def mark_articles_as_read_by_sub(bulk_q: BulkUpdateQueue, sub_id: str) -> int:
    count = 0
    for article in generate_articles_by_sub(bulk_q.connection, sub_id, unread_only=True):
        article.toggle_prop(Article.PROP_UNREAD, False)
        bulk_q.enqueue_flex(article)
        count += 1

    return count

def mark_articles_as_read_by_folder(bulk_q: BulkUpdateQueue, folder_id: str) -> int:
    for article in generate_articles_by_folder(bulk_q.connection, folder_id, unread_only=True):
        article.toggle_prop(Article.PROP_UNREAD, False)
        bulk_q.enqueue_flex(article)

def mark_articles_as_read_by_user(bulk_q: BulkUpdateQueue, user_id: str) -> int:
    for article in generate_articles_by_user(bulk_q.connection, user_id, unread_only=True):
        article.toggle_prop(Article.PROP_UNREAD, False)
        bulk_q.enqueue_flex(article)
