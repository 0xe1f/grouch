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
from datatype import Article
from datatype import FlexObject
from datatype import Folder
from datatype import Subscription
from datatype import User
from store import BulkUpdateQueue
from store import find_articles_by_id
from store import find_folders_by_id
from store import find_subs_by_id
from store import find_user_by_username
from tasks.objects import TaskContext
from tasks.objects import TaskException
import tasks.async_tasks as async_tasks

# General/multiple

def objects_rename(
    task_context: TaskContext,
    object_id: str|None,
    title: str|None,
):
    if not object_id:
        raise TaskException(f"Missing object id")
    elif not title:
        raise TaskException(f"Missing title")

    # FIXME!! validate title

    doc_type = FlexObject.extract_doc_type(object_id)
    with BulkUpdateQueue(task_context.connection) as bulk_q:
        if doc_type == Subscription.DOC_TYPE:
            owner_id = Subscription.extract_owner_id(object_id)
            if owner_id != task_context.user_id:
                raise TaskException(f"Unauthorized sub ({owner_id}!={task_context.user_id})")
            obj = first_or_none(find_subs_by_id(task_context.connection, object_id))
            if not obj:
                raise TaskException(f"No subscription with id {object_id}")
            obj.title = title
            bulk_q.enqueue_flex(obj)
        elif doc_type == Folder.DOC_TYPE:
            owner_id = Folder.extract_owner_id(object_id)
            if owner_id != task_context.user_id:
                raise TaskException(f"Unauthorized folder ({owner_id}!={task_context.user_id})")
            obj = first_or_none(find_folders_by_id(task_context.connection, object_id))
            if not obj:
                raise TaskException(f"No folder with id {object_id}")
            obj.title = title
            bulk_q.enqueue_flex(obj)
        else:
            raise TaskException(f"Unrecognized doc_type: {doc_type}")

# Articles

def articles_set_property(
    task_context: TaskContext,
    article_id: str|None,
    prop_name: str|None,
    is_set: bool
) -> Article:
    if not article_id:
        raise TaskException(f"Missing article id")

    owner_id = Article.extract_owner_id(article_id)
    conn = task_context.connection
    if owner_id != task_context.user_id:
        raise TaskException(f"Unauthorized article ({owner_id}!={task_context.user_id})")

    article = first_or_none(find_articles_by_id(conn, article_id))
    if not article:
        raise TaskException(f"No article with id {article_id}")

    if is_set != (prop_name in article.props):
        with BulkUpdateQueue(conn) as bulk_q:
            if prop_name == Article.PROP_UNREAD:
                # Need to also update sub
                if not (sub := first_or_none(find_subs_by_id(conn, article.subscription_id))):
                    raise TaskException(f"No sub with id {article.subscription_id}")
                sub.unread_count += 1 if is_set else -1
                bulk_q.enqueue_flex(sub)
            article.toggle_prop(prop_name, is_set)
            bulk_q.enqueue_flex(article)

def articles_set_tags(
    task_context: TaskContext,
    article_id: str|None,
    tags: list[str]|None,
) -> Article:
    if not article_id:
        raise TaskException(f"Missing article id")

    # FIXME!! check each for length

    new_tags = []
    if tags:
        # Extract unique tags, after trimming each for spaces
        new_tags = list(set([tag.strip() for tag in arg.tags]))
        if len(new_tags) > 5:
            raise TaskException(f"Too many tags ({len(new_tags)})")

    owner_id = Article.extract_owner_id(article_id)
    if owner_id != task_context.user_id:
        raise TaskException(f"Unauthorized article ({owner_id}!={task_context.user_id})")

    article = first_or_none(find_articles_by_id(task_context.connection, article_id))
    if not article:
        raise TaskException(f"Article not found ({article_id})")

    with BulkUpdateQueue(task_context.connection) as bulk_q:
        article.tags = new_tags
        bulk_q.enqueue_flex(article)

    return article

# Folders

def folders_create(
    task_context: TaskContext,
    title: str|None,
):
    if not title:
        raise TaskException(f"Missing title")

    # FIXME: validate for length

    with BulkUpdateQueue(task_context.connection) as bulk_q:
        folder = Folder()
        folder.title = title
        folder.user_id = task_context.user_id
        bulk_q.enqueue_flex(folder)

def folders_delete(
    task_context: TaskContext,
    folder_id: str|None,
):
    if not folder_id:
        raise TaskException(f"Missing id")

    if (owner_id := Folder.extract_owner_id(folder_id)) != task_context.user_id:
        raise TaskException(f"Unauthorized object ({owner_id}!={task_context.user_id})")

    # Clean up asynchronously
    task_context.queue_async(async_tasks.folders_delete, task_context, folder_id)

# Subs

def subs_move(
    task_context: TaskContext,
    sub_id: str|None,
    dest_id: str|None,
):
    if not sub_id:
        raise TaskException(f"Missing id")
    elif (sub_owner_id := Subscription.extract_owner_id(sub_id)) != task_context.user_id:
        raise TaskException(f"Unauthorized source ({sub_owner_id}!={task_context.user_id})")
    elif not (sub := first_or_none(find_subs_by_id(task_context.connection, sub_id))):
        raise TaskException(f"Sub ({sub_id}) does not exist")

    if dest_id:
        if (dest_owner_id := Folder.extract_owner_id(dest_id)) != task_context.user_id:
            raise TaskException(f"Unauthorized destination ({dest_owner_id}!={task_context.user_id})")

        if not first_or_none(find_folders_by_id(task_context.connection, dest_id)):
            raise TaskException(f"Destination ({dest_id}) does not exist")

    # Move the subscription
    with BulkUpdateQueue(task_context.connection) as bulk_q:
        sub.folder_id = dest_id or None
        bulk_q.enqueue_flex(sub)

    # Move the articles asynchronously
    if bulk_q.written_count > 0:
        task_context.queue_async(async_tasks.articles_move, task_context, sub_id, dest_id)

def subs_unsubscribe(
    task_context: TaskContext,
    sub_id: str|None,
):
    if not sub_id:
        raise TaskException(f"Missing id")

    if (owner_id := Subscription.extract_owner_id(sub_id)) != task_context.user_id:
        raise TaskException(f"Unauthorized sub_id ({owner_id}!={ task_context.user_id})")

    # Clean up asynchronously
    task_context.queue_async(async_tasks.subs_unsubscribe, task_context, sub_id)

# User

def users_authenticate(
    task_context: TaskContext,
    username: str,
    password: str,
) -> User:
    if not (user := find_user_by_username(task_context.connection, username)):
        raise TaskException("User not found")
    elif not user.plaintext_matching_stored(password):
        raise TaskException("Password mismatch")

    return user
