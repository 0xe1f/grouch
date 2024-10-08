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
from concurrent.futures import as_completed
from concurrent.futures import ThreadPoolExecutor
from entity import Feed
from parser import ParseResult
from parser import parse_feed
from dao import BulkUpdateQueue
import datetime
import logging
import time

def import_feeds(
    bulk_q: BulkUpdateQueue,
    *feed_urls: str,
) -> set[str]:
    successful, _ = _fetch_feeds(*feed_urls)
    import_feed_results(bulk_q, *successful)

    return [result.url for result in successful]

def import_feed_results(
    bulk_q: BulkUpdateQueue,
    *results: ParseResult,
):
    if not results:
        return set()

    feed_count = 0
    entry_count = 0

    for result in results:
        feed = result.feed
        feed_count += 1
        feed.digest = feed.computed_digest()
        bulk_q.enqueue(feed)

        entry_count += len(result.entries)
        for entry in result.entries:
            entry.feed_id = result.feed.id
            entry.digest = entry.computed_digest()

            bulk_q.enqueue(entry)

def refresh_feeds(
    tc: TaskContext,
    freshness_seconds: int,
):
    now = datetime.datetime.now()
    stale_start = now - datetime.timedelta(seconds=freshness_seconds)

    pending_fetch = []
    fetch_batch_max = 40

    with tc.dao.new_q() as bulk_q:
        # TODO: probably good to set some sort of max limit
        for feed in tc.dao.feeds.iter_updated_before(stale_start=stale_start.timestamp()):
            pending_fetch.append(feed)
            if len(pending_fetch) >= fetch_batch_max:
                _freshen_stale_feed(tc, bulk_q, *pending_fetch)
                pending_fetch.clear()

        if pending_fetch:
            _freshen_stale_feed(tc, bulk_q, *pending_fetch)
            pending_fetch.clear()

def _freshen_stale_feed(
    tc: TaskContext,
    bulk_q: BulkUpdateQueue,
    *feeds: Feed,
):
    local_feed_map = { feed.feed_url:feed for feed in feeds }

    feeds_changed = 0
    entries_changed = 0
    successful, _ = _fetch_feeds(*local_feed_map.keys())

    for result in successful:
        remote_feed = result.feed
        local_feed = local_feed_map[remote_feed.feed_url]
        if remote_feed.digest != local_feed.digest:
            feeds_changed += 1
            remote_feed.rev = local_feed.rev
            remote_feed.id = local_feed.id
            remote_feed.digest = remote_feed.computed_digest()

            bulk_q.enqueue(remote_feed)

        remote_entry_map = { entry.entry_uid:entry for entry in result.entries }
        for local_entry in tc.dao.entries.iter_by_uid(local_feed.id, *remote_entry_map.keys()):
            remote_entry = remote_entry_map[local_entry.entry_uid]
            if remote_entry.digest != local_entry.digest:
                remote_entry.feed_id = local_feed.id
                remote_entry.rev = local_entry.rev
                remote_entry.id = local_entry.id
                remote_entry.digest = remote_entry.computed_digest()

                bulk_q.enqueue(remote_entry)
                entries_changed += 1
                del remote_entry_map[local_entry.entry_uid]
            else:
                del remote_entry_map[local_entry.entry_uid]

        for remote_entry in remote_entry_map.values():
            remote_entry.feed_id = local_feed.id
            remote_entry.digest = remote_entry.computed_digest()
            bulk_q.enqueue(remote_entry)
            entries_changed += 1

    logging.debug(f"{feeds_changed} feeds and {entries_changed} entries updated")

def _fetch_feeds(
    *feed_urls: str,
) -> tuple[list[ParseResult], list[ParseResult]]:
    start = time.time()

    successful = []
    failed = []
    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_url = { executor.submit(parse_feed, url):url for url in feed_urls }
        for future in as_completed(future_to_url):
            url = future_to_url[future]
            try:
                result = future.result()
                if result.feed:
                    successful.append(result)
                else:
                    failed.append(result)
            except Exception as e:
                logging.exception(f"Failed to load {url}", e)

    logging.debug(f"Fetched {len(feed_urls)} in {"%.2f" % (time.time() - start)}s; {len(successful)} OK, {len(failed)} failed")

    return successful, failed
