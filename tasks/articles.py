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

from .celery_app import celery_app
from .celery_app import get_dao
from .celery_app import per_user
from time import time
import logging


@celery_app.task(bind=True, max_retries=30, default_retry_delay=10)
@per_user
def subs_mark_read_by_user(self, user_id: str):
    dao = get_dao()
    start_time = time()
    with dao.new_q() as bulk_q:
        dao.articles.mark_as_read_by_user(bulk_q, user_id)
    logging.info(f"Marked {bulk_q.written_count}/{bulk_q.enqueued_count} objects ({time() - start_time:.2}s)")


@celery_app.task(bind=True, max_retries=30, default_retry_delay=10)
@per_user
def subs_mark_read_by_folder(self, user_id: str, folder_id: str):
    dao = get_dao()
    start_time = time()
    with dao.new_q() as bulk_q:
        dao.articles.mark_as_read_by_folder(bulk_q, folder_id)
    logging.info(f"Marked {bulk_q.written_count}/{bulk_q.enqueued_count} objects ({time() - start_time:.2}s)")


@celery_app.task(bind=True, max_retries=30, default_retry_delay=10)
@per_user
def subs_mark_read_by_sub(self, user_id: str, sub_id: str):
    dao = get_dao()
    start_time = time()
    with dao.new_q() as bulk_q:
        dao.articles.mark_as_read_by_sub(bulk_q, sub_id)
    logging.info(f"Marked {bulk_q.written_count}/{bulk_q.enqueued_count} objects ({time() - start_time:.2}s)")


@celery_app.task(bind=True, max_retries=30, default_retry_delay=10)
@per_user
def articles_move(self, user_id: str, sub_id: str, dest_folder_id: str | None):
    dao = get_dao()
    start_time = time()
    with dao.new_q() as bulk_q:
        dao.articles.move_by_sub(bulk_q, sub_id, dest_folder_id)
    logging.info(f"Moved {bulk_q.written_count}/{bulk_q.enqueued_count} articles ({time() - start_time:.2}s)")


@celery_app.task(bind=True, max_retries=30, default_retry_delay=10)
@per_user
def articles_remove_tag(self, user_id: str, tag: str):
    dao = get_dao()
    start_time = time()
    with dao.new_q() as bulk_q:
        dao.articles.remove_all_tags_by_user_by_name(bulk_q, user_id, tag)
    logging.info(f"Updated {bulk_q.written_count}/{bulk_q.enqueued_count} articles ({time() - start_time:.2}s)")
