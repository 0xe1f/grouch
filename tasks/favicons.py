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

from entity.favicon import Favicon
from entity.favicon import STATUS_FAILED
from entity.favicon import STATUS_MISSING
from entity.favicon import STATUS_OK
from parser.favicon import build_display_png
from parser.favicon import discover_favicon
from parser.favicon import hash_bytes
from common.config import load_config
from tasks.celery_app import celery_app
from tasks.celery_app import get_dao
from tasks.celery_app import get_redis
import logging
import time

_config = load_config()
FAVICON_OK_REFRESH_DAYS = int(_config.get("FAVICON_OK_REFRESH_DAYS", 30))
FAVICON_RETRY_DAYS = int(_config.get("FAVICON_RETRY_DAYS", 7))
FAVICON_QUEUE_TTL_SECS = 600
FAVICON_LOCK_TTL_SECS = 600


def is_favicon_due(favicon: Favicon | None, now: float | None = None) -> bool:
    now = now if now is not None else time.time()
    if favicon is None or not favicon.checked_at:
        return True
    if favicon.status == STATUS_OK and favicon.has_display_attachment():
        return now - float(favicon.checked_at) >= FAVICON_OK_REFRESH_DAYS * 86400
    return now - float(favicon.checked_at) >= FAVICON_RETRY_DAYS * 86400


def claim_favicon_enqueue(feed_id: str) -> bool:
    redis = get_redis()
    return bool(redis.set(f"favicon_queued:{feed_id}", 1, nx=True, ex=FAVICON_QUEUE_TTL_SECS))


def _acquire_favicon_lock(feed_id: str) -> bool:
    redis = get_redis()
    return bool(redis.set(f"favicon_lock:{feed_id}", 1, nx=True, ex=FAVICON_LOCK_TTL_SECS))


def _release_favicon_lock(feed_id: str):
    get_redis().delete(f"favicon_lock:{feed_id}")


def _clear_favicon_claim(feed_id: str):
    get_redis().delete(f"favicon_queued:{feed_id}")


@celery_app.task(bind=True, name="tasks.favicons.favicon_fetch")
def favicon_fetch(self, feed_id: str, notify_user_id: str | None = None):
    if not _acquire_favicon_lock(feed_id):
        logging.info("Favicon lock held for %s; skipping", feed_id)
        return

    try:
        _run_favicon_fetch(feed_id, notify_user_id=notify_user_id)
    finally:
        _release_favicon_lock(feed_id)
        _clear_favicon_claim(feed_id)


def _run_favicon_fetch(feed_id: str, notify_user_id: str | None = None):
    dao = get_dao()
    feeds = dao.feeds.find_by_id(feed_id)
    if not feeds:
        logging.warning("Favicon fetch: feed not found %s", feed_id)
        return
    feed = feeds[0]

    existing = dao.favicons.find_by_feed_id(feed_id)
    source = discover_favicon(feed.site_url, feed.feed_url)
    now = time.time()

    if source is None:
        fav = existing or Favicon()
        fav.feed_id = feed_id
        # Keep last-good display if we already had one
        if existing and existing.status == STATUS_OK and existing.has_display_attachment():
            fav.status = STATUS_OK
            fav.source_hash = existing.source_hash
            fav.content_hash = existing.content_hash
            fav.content_type = existing.content_type
            fav.source_url = existing.source_url
            fav.width = existing.width
            fav.height = existing.height
            if existing.rev:
                fav.rev = existing.rev
            if existing.id:
                fav.id = existing.id
        else:
            fav.status = STATUS_MISSING
        fav.checked_at = now
        dao.favicons.save_meta(fav)
        return

    source_hash = hash_bytes(source.data)
    if (existing and existing.status == STATUS_OK
            and existing.source_hash == source_hash
            and existing.has_display_attachment()):
        existing.checked_at = now
        dao.favicons.save_meta(existing)
        return

    display = build_display_png(source.data, source.content_type)
    if display is None:
        fav = existing or Favicon()
        fav.feed_id = feed_id
        if existing and existing.status == STATUS_OK and existing.has_display_attachment():
            fav.status = STATUS_OK
            fav.source_hash = existing.source_hash
            fav.content_hash = existing.content_hash
            fav.content_type = existing.content_type
            fav.source_url = existing.source_url
            fav.width = existing.width
            fav.height = existing.height
            if existing.rev:
                fav.rev = existing.rev
            if existing.id:
                fav.id = existing.id
        else:
            fav.status = STATUS_FAILED
        fav.checked_at = now
        dao.favicons.save_meta(fav)
        return

    fav = existing or Favicon()
    fav.feed_id = feed_id
    fav.status = STATUS_OK
    fav.checked_at = now
    fav.source_url = source.source_url
    fav.content_type = source.content_type
    fav.source_hash = source_hash
    fav.content_hash = display.content_hash
    fav.width = display.width
    fav.height = display.height
    if existing and existing.rev:
        fav.rev = existing.rev
    if existing and existing.id:
        fav.id = existing.id

    dao.favicons.save_with_attachments(
        fav,
        original=source.data,
        original_content_type=source.content_type,
        display=display.png,
    )
    _notify_favicon(dao, feed_id, display.content_hash, notify_user_id=notify_user_id)


def _notify_favicon(
    dao,
    feed_id: str,
    content_hash: str,
    notify_user_id: str | None = None,
):
    from tasks.worker_notify import notify as send_notification

    from urllib.parse import quote
    url = f"/api/feeds/favicon?feed_id={quote(feed_id, safe='')}&v={content_hash[:16]}"
    payload = {"feedId": feed_id, "url": url}
    user_ids = set(dao.subs.iter_user_ids_by_feed(feed_id))
    if notify_user_id:
        user_ids.add(notify_user_id)
    for user_id in user_ids:
        send_notification(user_id, "favicon", payload)
