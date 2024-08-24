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

from common import first_or_none
from port import PortDoc
from tasks.objects import TaskContext
from time import time
import logging
import tasks.folders as tasks_folders
import tasks.subscriptions as tasks_sub

# Subs

def subs_sync(
    tc: TaskContext,
):
    with tc.dao.new_q() as bulk_q:
        tasks_sub.sync_subs(tc, bulk_q, tc.user_id)

    logging.debug(f"{bulk_q.written_count}/{bulk_q.enqueued_count} records written; {bulk_q.commit_count} commits")

    if tc._completion_message:
        tc.send_message(tc._completion_message)

def subs_subscribe_url(
    tc: TaskContext,
    url: str,
):
    tasks_sub.subscribe_user_unknown_url(tc, tc.user_id, url)

    if tc._completion_message:
        tc.send_message(tc._completion_message)

def subs_import(
    tc: TaskContext,
    doc: PortDoc,
):
    tasks_sub.import_user_subs(tc, tc.user_id, doc)

    if tc._completion_message:
        tc.send_message(tc._completion_message)

def subs_unsubscribe(
    tc: TaskContext,
    *sub_ids: int,
):
    tasks_sub.unsubscribe(tc, *sub_ids)

    if tc._completion_message:
        tc.send_message(tc._completion_message)

def subs_mark_read_by_user(
    tc: TaskContext,
):
    start_time = time()
    with tc.dao.new_q() as bulk_q:
        tc.dao.articles.mark_as_read_by_user(bulk_q, tc.user_id)
        for sub in tc.dao.subs.iter_by_user(tc.user_id):
            sub.unread_count = 0
            bulk_q.enqueue(sub)

    logging.info(f"Marked {bulk_q.written_count}/{bulk_q.enqueued_count} objects ({time() - start_time:.2}s)")

    if tc._completion_message:
        tc.send_message(tc._completion_message)

def subs_mark_read_by_folder(
    tc: TaskContext,
    folder_id: str,
):
    start_time = time()
    with tc.dao.new_q() as bulk_q:
        tc.dao.articles.mark_as_read_by_folder(bulk_q, folder_id)
        for sub in tc.dao.subs.iter_by_folder(folder_id):
            # TODO: this is potentially inacurate
            sub.unread_count = 0
            bulk_q.enqueue(sub)

    logging.info(f"Marked {bulk_q.written_count}/{bulk_q.enqueued_count} objects ({time() - start_time:.2}s)")

    if tc._completion_message:
        tc.send_message(tc._completion_message)

def subs_mark_read_by_sub(
    tc: TaskContext,
    sub_id: str,
):
    start_time = time()
    with tc.dao.new_q() as bulk_q:
        changed = tc.dao.articles.mark_as_read_by_sub(bulk_q, sub_id)
        if sub := first_or_none(tc.dao.subs.find_by_id(sub_id)):
            sub.unread_count -= changed
            bulk_q.enqueue(sub)

    logging.info(f"Marked {bulk_q.written_count}/{bulk_q.enqueued_count} objects ({time() - start_time:.2}s)")

    if tc._completion_message:
        tc.send_message(tc._completion_message)

# Articles

def articles_move(
    tc: TaskContext,
    sub_id: str,
    dest_folder_id: str|None,
):
    start_time = time()
    with tc.dao.new_q() as bulk_q:
        tc.dao.articles.move_by_sub(bulk_q, sub_id, dest_folder_id)
    logging.info(f"Moved {bulk_q.written_count}/{bulk_q.enqueued_count} articles ({time() - start_time:.2}s)")

    if tc._completion_message:
        tc.send_message(tc._completion_message)

def articles_remove_tag(
    tc: TaskContext,
    tag: str,
):
    start_time = time()
    with tc.dao.new_q() as bulk_q:
        tc.dao.articles.remove_all_tags_by_user_by_name(bulk_q, tag)
    logging.info(f"Updated {bulk_q.written_count}/{bulk_q.enqueued_count} articles ({time() - start_time:.2}s)")

    if tc._completion_message:
        tc.send_message(tc._completion_message)

# Folders

def folders_delete(tc: TaskContext, folder_id: str):
    tasks_folders.delete_folder(tc, folder_id)

    if tc._completion_message:
        tc.send_message(tc._completion_message)
