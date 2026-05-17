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

from .subscriptions import remove_subscriptions
from .celery_app import celery_app
from .celery_app import get_dao
from .celery_app import per_user
from common import first_or_none
from dao import Database
from time import time
import logging


def delete_folder(
    dao: Database,
    folder_id: str,
):
    start_time = time()
    all_subscriptions_removed = True

    with dao.new_q() as bulk_q:
        if sub_ids := dao.subs.find_ids_by_folder(folder_id):
            if not remove_subscriptions(dao, bulk_q, *sub_ids):
                all_subscriptions_removed = False
                logging.warning(f"Not all subscriptions were removed")

        if all_subscriptions_removed:
            # Don't remove folder if one or more subs were left
            if folder := first_or_none(dao.folders.find_by_id(folder_id)):
                folder.mark_deleted()
                bulk_q.enqueue(folder)
            else:
                logging.warning(f"No folder with id {folder_id}")

    logging.info(f"Delete folder {folder_id}: {bulk_q.written_count}/{bulk_q.enqueued_count} objects written ({time() - start_time:.2}s)")


@celery_app.task(bind=True, max_retries=30, default_retry_delay=10)
@per_user
def folders_delete(self, user_id: str, folder_id: str):
    delete_folder(get_dao(), folder_id)
