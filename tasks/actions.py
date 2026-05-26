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
from entity import Invite
from entity import Subscription
from entity import User
import bcrypt
import datetime
from datetime import date
from datetime import time as dt_time
from datetime import timedelta
from datetime import timezone
import enum
import logging
from parser.consts import MAX_TITLE_LEN

logger = logging.getLogger(__name__)


MAX_TAG_LEN = 32
MAX_TAG_COUNT = 8


class ActionError(Exception):

    class Code(enum.Enum):
        BAD_REQUEST = "bad_request"
        UNAUTHORIZED = "unauthorized"
        NOT_FOUND = "not_found"
        SERVER_ERROR = "server_error"

    BAD_REQUEST = Code.BAD_REQUEST
    UNAUTHORIZED = Code.UNAUTHORIZED
    NOT_FOUND = Code.NOT_FOUND
    SERVER_ERROR = Code.SERVER_ERROR

    def __init__(self, message: str, code: Code = Code.BAD_REQUEST, *args: object) -> None:
        super().__init__(message, *args)
        self._message = message
        self._code = code

    @property
    def message(self) -> str | None:
        return self._message

    @property
    def code(self) -> Code:
        return self._code


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
    title = (title or "").strip()
    if not title:
        raise ActionError(f"Missing title")
    if len(title) > MAX_TITLE_LEN:
        raise ActionError(f"Title exceeds maximum length ({MAX_TITLE_LEN} characters)")

    doc_type = Entity.extract_doc_type(object_id)
    with dao.new_q() as bulk_q:
        if doc_type == Subscription.DOC_TYPE:
            owner_id = Subscription.extract_owner_id(object_id)
            if owner_id != user_id:
                raise ActionError(f"Unauthorized sub ({owner_id}!={user_id})", ActionError.UNAUTHORIZED)
            obj = first_or_none(dao.subs.find_by_id(object_id))
            if not obj:
                raise ActionError(f"No subscription with id {object_id}", ActionError.NOT_FOUND)
            obj.title = title
            bulk_q.enqueue(obj)
        elif doc_type == Folder.DOC_TYPE:
            owner_id = Folder.extract_owner_id(object_id)
            if owner_id != user_id:
                raise ActionError(f"Unauthorized folder ({owner_id}!={user_id})", ActionError.UNAUTHORIZED)
            obj = first_or_none(dao.folders.find_by_id(object_id))
            if not obj:
                raise ActionError(f"No folder with id {object_id}", ActionError.NOT_FOUND)
            obj.title = title
            bulk_q.enqueue(obj)
        else:
            raise ActionError(f"Unrecognized doc_type: {doc_type}", ActionError.SERVER_ERROR)


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
        raise ActionError(f"Unauthorized article ({owner_id}!={user_id})", ActionError.UNAUTHORIZED)

    article = first_or_none(dao.articles.find_by_id(article_id))
    if not article:
        raise ActionError(f"No article with id {article_id}", ActionError.NOT_FOUND)

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

    new_tags = []
    if tags:
        # Extract unique tags, after trimming each for spaces
        new_tags = list(set([tag.strip() for tag in tags]))
        if len(new_tags) > MAX_TAG_COUNT:
            raise ActionError(f"Too many tags (max {MAX_TAG_COUNT})")
        for tag in new_tags:
            if len(tag) > MAX_TAG_LEN:
                raise ActionError(f"Tag exceeds maximum length ({MAX_TAG_LEN} characters)")

    owner_id = Article.extract_owner_id(article_id)
    if owner_id != user_id:
        raise ActionError(f"Unauthorized article ({owner_id}!={user_id})", ActionError.UNAUTHORIZED)

    article = first_or_none(dao.articles.find_by_id(article_id))
    if not article:
        raise ActionError(f"Article not found ({article_id})", ActionError.NOT_FOUND)

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
    title = title.strip()
    if not title:
        raise ActionError(f"Missing title")
    if len(title) > MAX_TITLE_LEN:
        raise ActionError(f"Title exceeds maximum length ({MAX_TITLE_LEN} characters)")

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
        raise ActionError(f"Unauthorized object ({owner_id}!={user_id})", ActionError.UNAUTHORIZED)

    from tasks.folders import folders_delete as _folders_delete_task
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
        raise ActionError(f"Unauthorized source ({sub_owner_id}!={user_id})", ActionError.UNAUTHORIZED)
    elif not (sub := first_or_none(dao.subs.find_by_id(sub_id))):
        raise ActionError(f"Sub ({sub_id}) does not exist", ActionError.NOT_FOUND)

    if dest_id:
        if (dest_owner_id := Folder.extract_owner_id(dest_id)) != user_id:
            raise ActionError(f"Unauthorized destination ({dest_owner_id}!={user_id})", ActionError.UNAUTHORIZED)

        if not first_or_none(dao.folders.find_by_id(dest_id)):
            raise ActionError(f"Destination ({dest_id}) does not exist", ActionError.NOT_FOUND)

    # Move the subscription
    with dao.new_q() as bulk_q:
        sub.folder_id = dest_id or None
        bulk_q.enqueue(sub)

    # Move the articles asynchronously
    if bulk_q.written_count > 0:
        from tasks.articles import articles_move as _articles_move_task
        _articles_move_task.delay(user_id, sub_id, dest_id)


def subs_unsubscribe(
    dao: Database,
    user_id: str,
    sub_id: str | None,
):
    if not sub_id:
        raise ActionError(f"Missing id")

    if (owner_id := Subscription.extract_owner_id(sub_id)) != user_id:
        raise ActionError(f"Unauthorized sub_id ({owner_id}!={user_id})", ActionError.UNAUTHORIZED)

    from tasks.subscriptions import subs_unsubscribe as _subs_unsubscribe_task
    _subs_unsubscribe_task.delay(user_id, [sub_id])


def subs_sync(
    dao: Database,
    user_id: str,
    ref_time: datetime.datetime,
    timeout_secs: int,
) -> datetime.datetime:
    if not (user := dao.users.find_by_id(user_id)):
        raise ActionError("User not found", ActionError.SERVER_ERROR)

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

    from tasks.subscriptions import subs_sync as _subs_sync_task
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
        raise ActionError("User not found", ActionError.UNAUTHORIZED)
    elif not user.plaintext_matching_stored(password):
        raise ActionError("Password mismatch", ActionError.UNAUTHORIZED)

    return user


# ---------------------------------------------------------------------------
# Invites
# ---------------------------------------------------------------------------

INVITE_INVALID_MESSAGE = "This invitation is invalid or has expired."

def invites_send(
    dao: Database,
    inviter_user_id: str,
    invitee_email: str,
    expiry_days: int = 14,
) -> Invite:
    existing = dao.invites.find_by_invitee_email(invitee_email)
    for inv in existing:
        if inv.status == Invite.STATUS_PENDING:
            raise ActionError(f"An active invitation already exists for {invitee_email}")

    now = datetime.datetime.now(tz=timezone.utc)
    sent_at = now.timestamp()
    sent_date = now.date()
    expiry_dt = datetime.datetime.combine(
        sent_date + timedelta(days=expiry_days + 1),
        dt_time.min,
        tzinfo=timezone.utc,
    )
    expiry_date = expiry_dt.timestamp()

    invite = Invite()
    invite.inviter_user_id = inviter_user_id
    invite.invitee_email = invitee_email
    invite.status = Invite.STATUS_PENDING
    invite.sent_at = sent_at
    invite.expiry_date = expiry_date

    if not dao.invites.create(invite):
        raise ActionError("Failed to create invitation", ActionError.SERVER_ERROR)

    try:
        from common.email import send_invite
        send_invite(
            token=invite.token,
            to_address=invitee_email,
            expiry_timestamp=expiry_date,
        )
    except Exception as exc:
        logger.error("Failed to send invite email to %s: %s", invitee_email, exc)
        raise ActionError("Invitation created but email could not be sent. Please try again.", ActionError.SERVER_ERROR)

    return invite


def invites_cancel(
    dao: Database,
    invite_id: str,
) -> Invite:
    invite = dao.invites.find_by_token(invite_id.removeprefix("invite::"))
    if not invite:
        raise ActionError("Invitation not found", ActionError.NOT_FOUND)
    if invite.status != Invite.STATUS_PENDING:
        raise ActionError("Only pending invitations can be cancelled")

    invite.status = Invite.STATUS_CANCELLED
    dao.invites.update(invite)
    return invite


def invites_resend(
    dao: Database,
    invite_id: str,
    inviter_user_id: str,
    expiry_days: int = 14,
) -> Invite:
    invite = dao.invites.find_by_token(invite_id.removeprefix("invite::"))
    if not invite:
        raise ActionError("Invitation not found", ActionError.NOT_FOUND)
    if invite.status == Invite.STATUS_ACCEPTED:
        raise ActionError("Cannot resend an accepted invitation")

    invitee_email = invite.invitee_email

    invite.status = Invite.STATUS_CANCELLED
    dao.invites.update(invite)

    return invites_send(dao, inviter_user_id, invitee_email, expiry_days)


def invites_validate(
    dao: Database,
    token: str,
    submitted_email: str,
) -> Invite:
    invite = dao.invites.find_by_token(token)
    now = datetime.datetime.now(tz=timezone.utc).timestamp()

    if not invite:
        raise ActionError(INVITE_INVALID_MESSAGE)

    if invite.status != Invite.STATUS_PENDING:
        raise ActionError(INVITE_INVALID_MESSAGE)

    if invite.expiry_date <= now:
        if invite.status == Invite.STATUS_PENDING:
            logger.warning(
                "Invite %s has expired (expiry_date=%s) but status is still pending; "
                "sweep may not have run yet",
                invite.id,
                invite.expiry_date,
            )
        raise ActionError(INVITE_INVALID_MESSAGE)

    if invite.invitee_email.lower() != submitted_email.lower():
        raise ActionError(INVITE_INVALID_MESSAGE)

    return invite


def invites_mark_accepted(
    dao: Database,
    invite: Invite,
    user_id: str,
):
    invite.status = Invite.STATUS_ACCEPTED
    invite.accepted_at = datetime.datetime.now(tz=timezone.utc).timestamp()
    invite.accepted_user_id = user_id
    dao.invites.update(invite)


def invites_expire_pending(
    dao: Database,
):
    midnight_utc = datetime.datetime.combine(
        datetime.datetime.now(tz=timezone.utc).date(),
        dt_time.min,
        tzinfo=timezone.utc,
    ).timestamp()

    expired = dao.invites.find_expired_pending(midnight_utc)
    logger.info("Expiry sweep: marking %d invites as expired", len(expired))
    for invite in expired:
        invite.status = Invite.STATUS_EXPIRED
        dao.invites.update(invite)


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
