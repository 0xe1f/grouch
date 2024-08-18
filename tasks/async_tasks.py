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

from store import BulkUpdateQueue
from port import PortDoc
from tasks.objects import TaskContext
import logging
import tasks.articles as tasks_articles
import tasks.folders as tasks_folders
import tasks.subscriptions as tasks_sub

# Subs

def subs_sync(task_context: TaskContext):
    with BulkUpdateQueue(task_context.connection, track_ids=False) as bulk_q:
        tasks_sub.sync_subs(bulk_q, task_context.user_id)

    logging.debug(f"{bulk_q.written_count}/{bulk_q.enqueued_count} records written; {bulk_q.commit_count} commits")

def subs_subscribe_url(task_context: TaskContext, url: str):
    tasks_sub.subscribe_user_unknown_url(task_context.connection, task_context.user_id, url)

def subs_import(task_context: TaskContext, doc: PortDoc):
    tasks_sub.import_user_subs(task_context.connection, task_context.user_id, doc)

def subs_unsubscribe(task_context: TaskContext, *sub_ids: int):
    tasks_sub.unsubscribe(task_context.connection, *sub_ids)

def subs_mark_read_by_user(task_context: TaskContext):
    tasks_sub.mark_subs_read_by_user(task_context.connection, task_context.user_id)

def subs_mark_read_by_folder(task_context: TaskContext, folder_id: str):
    tasks_sub.mark_subs_read_by_folder(task_context.connection, folder_id)

def subs_mark_read_by_sub(task_context: TaskContext, sub_id: str):
    tasks_sub.mark_sub_read(task_context.connection, sub_id)

# Articles

def articles_move(task_context: TaskContext, sub_id: str, dest_folder_id: str|None):
    tasks_articles.move_articles(task_context.connection, sub_id, dest_folder_id)

def articles_remove_tag(task_context: TaskContext, tag: str):
    tasks_articles.remove_tag_from_articles(task_context.connection, tag)

# Folders

def folders_delete(task_context: TaskContext, folder_id: str):
    tasks_folders.delete_folder(task_context.connection, folder_id)
