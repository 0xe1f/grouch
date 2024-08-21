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

from .objects import TaskContext
from .subscriptions import remove_subscriptions
from common import first_or_none
from time import time
import logging

def delete_folder(
    tc: TaskContext,
    folder_id: str,
):
    start_time = time()
    all_subscriptions_removed = True

    with tc.dao.new_q() as bulk_q:
        if sub_ids := tc.dao.subs.find_ids_by_folder(folder_id):
            if not remove_subscriptions(tc, bulk_q, *sub_ids):
                all_subscriptions_removed = False
                logging.warning(f"Not all subscriptions were removed")

        if all_subscriptions_removed:
            # Don't remove folder if one or more subs were left
            if folder := first_or_none(tc.dao.folders.find_by_id(folder_id)):
                folder.mark_deleted()
                bulk_q.enqueue(folder)
            else:
                logging.warning(f"No folder with id {folder_id}")

    logging.info(f"Delete folder {folder_id}: {bulk_q.written_count}/{bulk_q.enqueued_count} objects written ({time() - start_time:.2}s)")
