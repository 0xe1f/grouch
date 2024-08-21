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
from dao import BulkUpdateQueue
from tasks.objects import TaskContext
from tasks.objects import TaskException
import datetime
import tasks.async_tasks as async_tasks

# General/multiple

def objects_rename(
    tc: TaskContext,
    object_id: str|None,
    title: str|None,
):
    if not object_id:
        raise TaskException(f"Missing object id")
    elif not title:
        raise TaskException(f"Missing title")

    # FIXME!! validate title

    doc_type = FlexObject.extract_doc_type(object_id)
    with tc.dao.new_q() as bulk_q:
        if doc_type == Subscription.DOC_TYPE:
            owner_id = Subscription.extract_owner_id(object_id)
            if owner_id != tc.user_id:
                raise TaskException(f"Unauthorized sub ({owner_id}!={tc.user_id})")
            obj = first_or_none(tc.dao.subs.find_by_id(object_id))
            if not obj:
                raise TaskException(f"No subscription with id {object_id}")
            obj.title = title
            bulk_q.enqueue_flex(obj)
        elif doc_type == Folder.DOC_TYPE:
            owner_id = Folder.extract_owner_id(object_id)
            if owner_id != tc.user_id:
                raise TaskException(f"Unauthorized folder ({owner_id}!={tc.user_id})")
            obj = first_or_none(tc.dao.folders.find_by_id(object_id))
            if not obj:
                raise TaskException(f"No folder with id {object_id}")
            obj.title = title
            bulk_q.enqueue_flex(obj)
        else:
            raise TaskException(f"Unrecognized doc_type: {doc_type}")

# Articles

def articles_set_property(
    tc: TaskContext,
    article_id: str|None,
    prop_name: str|None,
    is_set: bool
) -> Article:
    if not article_id:
        raise TaskException(f"Missing article id")

    owner_id = Article.extract_owner_id(article_id)
    if owner_id != tc.user_id:
        raise TaskException(f"Unauthorized article ({owner_id}!={tc.user_id})")

    article = first_or_none(tc.dao.articles.find_by_id(article_id))
    if not article:
        raise TaskException(f"No article with id {article_id}")

    if is_set != (prop_name in article.props):
        with tc.dao.new_q() as bulk_q:
            if prop_name == Article.PROP_UNREAD:
                # Need to also update sub
                if not (sub := first_or_none(tc.dao.subs.find_by_id(article.subscription_id))):
                    raise TaskException(f"No sub with id {article.subscription_id}")
                sub.unread_count += 1 if is_set else -1
                bulk_q.enqueue_flex(sub)
            article.toggle_prop(prop_name, is_set)
            bulk_q.enqueue_flex(article)

    return article

def articles_set_tags(
    tc: TaskContext,
    article_id: str|None,
    tags: list[str]|None,
) -> Article:
    if not article_id:
        raise TaskException(f"Missing article id")

    # FIXME!! check each for length

    new_tags = []
    if tags:
        # Extract unique tags, after trimming each for spaces
        new_tags = list(set([tag.strip() for tag in tags]))
        if len(new_tags) > 5:
            raise TaskException(f"Too many tags ({len(new_tags)})")

    owner_id = Article.extract_owner_id(article_id)
    if owner_id != tc.user_id:
        raise TaskException(f"Unauthorized article ({owner_id}!={tc.user_id})")

    article = first_or_none(tc.dao.articles.find_by_id(article_id))
    if not article:
        raise TaskException(f"Article not found ({article_id})")

    with tc.dao.new_q() as bulk_q:
        article.tags = new_tags
        bulk_q.enqueue_flex(article)

    return article

# Folders

def folders_create(
    tc: TaskContext,
    title: str|None,
):
    if not title:
        raise TaskException(f"Missing title")

    # FIXME: validate for length

    with tc.dao.new_q() as bulk_q:
        folder = Folder()
        folder.title = title
        folder.user_id = tc.user_id
        bulk_q.enqueue_flex(folder)

def folders_delete(
    tc: TaskContext,
    folder_id: str|None,
):
    if not folder_id:
        raise TaskException(f"Missing id")

    if (owner_id := Folder.extract_owner_id(folder_id)) != tc.user_id:
        raise TaskException(f"Unauthorized object ({owner_id}!={tc.user_id})")

    # Clean up asynchronously
    tc.queue_async(async_tasks.folders_delete, tc, folder_id)

# Subs

def subs_move(
    tc: TaskContext,
    sub_id: str|None,
    dest_id: str|None,
):
    if not sub_id:
        raise TaskException(f"Missing id")
    elif (sub_owner_id := Subscription.extract_owner_id(sub_id)) != tc.user_id:
        raise TaskException(f"Unauthorized source ({sub_owner_id}!={tc.user_id})")
    elif not (sub := first_or_none(tc.dao.subs.find_by_id(sub_id))):
        raise TaskException(f"Sub ({sub_id}) does not exist")

    if dest_id:
        if (dest_owner_id := Folder.extract_owner_id(dest_id)) != tc.user_id:
            raise TaskException(f"Unauthorized destination ({dest_owner_id}!={tc.user_id})")

        if not first_or_none(tc.dao.folders.find_by_id(dest_id)):
            raise TaskException(f"Destination ({dest_id}) does not exist")

    # Move the subscription
    with tc.dao.new_q() as bulk_q:
        sub.folder_id = dest_id or None
        bulk_q.enqueue_flex(sub)

    # Move the articles asynchronously
    if bulk_q.written_count > 0:
        tc.queue_async(async_tasks.articles_move, tc, sub_id, dest_id)

def subs_unsubscribe(
    tc: TaskContext,
    sub_id: str|None,
):
    if not sub_id:
        raise TaskException(f"Missing id")

    if (owner_id := Subscription.extract_owner_id(sub_id)) != tc.user_id:
        raise TaskException(f"Unauthorized sub_id ({owner_id}!={ tc.user_id})")

    # Clean up asynchronously
    tc.queue_async(async_tasks.subs_unsubscribe, tc, sub_id)

def subs_sync(
    tc: TaskContext,
    ref_time: datetime.datetime,
    timeout_secs: int,
) -> datetime.datetime:
    if not (user := tc.dao.users.find_by_id(tc.user_id)):
        raise TaskException("User not found")

    if last_sync := user.last_sync:
        last_sync_dt = datetime.datetime.fromtimestamp(last_sync)
        delta = ref_time - last_sync_dt
        if delta.total_seconds() < timeout_secs:
            return ref_time + delta
        else:
           last_sync = None

    if not last_sync:
        user.last_sync = ref_time.timestamp()
        with tc.dao.new_q() as bulk_q:
            bulk_q.enqueue_flex(user)

    tc.queue_async(async_tasks.subs_sync, tc)

    return ref_time + datetime.timedelta(seconds=timeout_secs)

# User

def users_authenticate(
    tc: TaskContext,
    username: str,
    password: str,
) -> User:
    if not (user := tc.dao.users.find_by_username(username)):
        raise TaskException("User not found")
    elif not user.plaintext_matching_stored(password):
        raise TaskException("Password mismatch")

    return user
