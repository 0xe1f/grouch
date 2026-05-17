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
from dao import Database
from entity import Article
from entity import Entity
from entity import Folder
from entity import Subscription
from entity import User
from tasks.articles import articles_move as _articles_move_task
from tasks.folders import folders_delete as _folders_delete_task
from tasks.subscriptions import subs_sync as _subs_sync_task
from tasks.subscriptions import subs_unsubscribe as _subs_unsubscribe_task
import bcrypt
import datetime


class ActionError(Exception):

    def __init__(self, message: str, *args: object) -> None:
        super().__init__(message, *args)
        self._message = message

    @property
    def message(self) -> str | None:
        return self._message


# ---------------------------------------------------------------------------
# General / multiple
# ---------------------------------------------------------------------------

def objects_rename(
    dao: Database,
    user_id: str,
    object_id: str | None,
    title: str | None,
):
    if not object_id:
        raise ActionError(f"Missing object id")
    elif not title:
        raise ActionError(f"Missing title")

    # FIXME!! validate title

    doc_type = Entity.extract_doc_type(object_id)
    with dao.new_q() as bulk_q:
        if doc_type == Subscription.DOC_TYPE:
            owner_id = Subscription.extract_owner_id(object_id)
            if owner_id != user_id:
                raise ActionError(f"Unauthorized sub ({owner_id}!={user_id})")
            obj = first_or_none(dao.subs.find_by_id(object_id))
            if not obj:
                raise ActionError(f"No subscription with id {object_id}")
            obj.title = title
            bulk_q.enqueue(obj)
        elif doc_type == Folder.DOC_TYPE:
            owner_id = Folder.extract_owner_id(object_id)
            if owner_id != user_id:
                raise ActionError(f"Unauthorized folder ({owner_id}!={user_id})")
            obj = first_or_none(dao.folders.find_by_id(object_id))
            if not obj:
                raise ActionError(f"No folder with id {object_id}")
            obj.title = title
            bulk_q.enqueue(obj)
        else:
            raise ActionError(f"Unrecognized doc_type: {doc_type}")


# ---------------------------------------------------------------------------
# Articles
# ---------------------------------------------------------------------------

def articles_set_property(
    dao: Database,
    user_id: str,
    article_id: str | None,
    prop_name: str | None,
    is_set: bool,
) -> Article:
    if not article_id:
        raise ActionError(f"Missing article id")

    owner_id = Article.extract_owner_id(article_id)
    if owner_id != user_id:
        raise ActionError(f"Unauthorized article ({owner_id}!={user_id})")

    article = first_or_none(dao.articles.find_by_id(article_id))
    if not article:
        raise ActionError(f"No article with id {article_id}")

    if is_set != (prop_name in article.props):
        with dao.new_q() as bulk_q:
            article.toggle_prop(prop_name, is_set)
            bulk_q.enqueue(article)

    return article


def articles_set_tags(
    dao: Database,
    user_id: str,
    article_id: str | None,
    tags: list[str] | None,
) -> Article:
    if not article_id:
        raise ActionError(f"Missing article id")

    # FIXME!! check each for length

    new_tags = []
    if tags:
        # Extract unique tags, after trimming each for spaces
        new_tags = list(set([tag.strip() for tag in tags]))
        if len(new_tags) > 5:
            raise ActionError(f"Too many tags ({len(new_tags)})")

    owner_id = Article.extract_owner_id(article_id)
    if owner_id != user_id:
        raise ActionError(f"Unauthorized article ({owner_id}!={user_id})")

    article = first_or_none(dao.articles.find_by_id(article_id))
    if not article:
        raise ActionError(f"Article not found ({article_id})")

    with dao.new_q() as bulk_q:
        article.tags = new_tags
        bulk_q.enqueue(article)

    return article


# ---------------------------------------------------------------------------
# Folders
# ---------------------------------------------------------------------------

def folders_create(
    dao: Database,
    user_id: str,
    title: str | None,
):
    if not title:
        raise ActionError(f"Missing title")

    # FIXME: validate for length

    with dao.new_q() as bulk_q:
        folder = Folder()
        folder.title = title
        folder.user_id = user_id
        bulk_q.enqueue(folder)


def folders_delete(
    dao: Database,
    user_id: str,
    folder_id: str | None,
):
    if not folder_id:
        raise ActionError(f"Missing id")

    if (owner_id := Folder.extract_owner_id(folder_id)) != user_id:
        raise ActionError(f"Unauthorized object ({owner_id}!={user_id})")

    _folders_delete_task.delay(user_id, folder_id)


# ---------------------------------------------------------------------------
# Subscriptions
# ---------------------------------------------------------------------------

def subs_move(
    dao: Database,
    user_id: str,
    sub_id: str | None,
    dest_id: str | None,
):
    if not sub_id:
        raise ActionError(f"Missing id")
    elif (sub_owner_id := Subscription.extract_owner_id(sub_id)) != user_id:
        raise ActionError(f"Unauthorized source ({sub_owner_id}!={user_id})")
    elif not (sub := first_or_none(dao.subs.find_by_id(sub_id))):
        raise ActionError(f"Sub ({sub_id}) does not exist")

    if dest_id:
        if (dest_owner_id := Folder.extract_owner_id(dest_id)) != user_id:
            raise ActionError(f"Unauthorized destination ({dest_owner_id}!={user_id})")

        if not first_or_none(dao.folders.find_by_id(dest_id)):
            raise ActionError(f"Destination ({dest_id}) does not exist")

    # Move the subscription
    with dao.new_q() as bulk_q:
        sub.folder_id = dest_id or None
        bulk_q.enqueue(sub)

    # Move the articles asynchronously
    if bulk_q.written_count > 0:
        _articles_move_task.delay(user_id, sub_id, dest_id)


def subs_unsubscribe(
    dao: Database,
    user_id: str,
    sub_id: str | None,
):
    if not sub_id:
        raise ActionError(f"Missing id")

    if (owner_id := Subscription.extract_owner_id(sub_id)) != user_id:
        raise ActionError(f"Unauthorized sub_id ({owner_id}!={user_id})")

    _subs_unsubscribe_task.delay(user_id, [sub_id])


def subs_sync(
    dao: Database,
    user_id: str,
    ref_time: datetime.datetime,
    timeout_secs: int,
) -> datetime.datetime:
    if not (user := dao.users.find_by_id(user_id)):
        raise ActionError("User not found")

    if last_sync := user.last_sync:
        last_sync_dt = datetime.datetime.fromtimestamp(last_sync)
        delta = ref_time - last_sync_dt
        if delta.total_seconds() < timeout_secs:
            return last_sync_dt + datetime.timedelta(seconds=timeout_secs)
        else:
            last_sync = None

    if not last_sync:
        user.last_sync = ref_time.timestamp()
        with dao.new_q() as bulk_q:
            bulk_q.enqueue(user)

    _subs_sync_task.delay(user_id, notify=True)

    return ref_time + datetime.timedelta(seconds=timeout_secs)


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------

def users_authenticate(
    dao: Database,
    user_id: str,
    username: str,
    password: str,
) -> User:
    if not (user := dao.users.find_by_username(username)):
        raise ActionError("User not found")
    elif not user.plaintext_matching_stored(password):
        raise ActionError("Password mismatch")

    return user


def users_create_user(
    dao: Database,
    user_id: str,
    username: str,
    email_address: str,
    password: str,
) -> User:
    salt = bcrypt.gensalt()

    user = User()
    user.username = username
    user.set_hashed_password(password, salt)
    user.email_address = email_address

    if not dao.users.create(user):
        raise ActionError("Cannot create user")

    return user
