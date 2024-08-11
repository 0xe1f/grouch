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

from concurrent.futures import as_completed
from concurrent.futures import ThreadPoolExecutor
from datatype import FeedContent
from parser import ParseResult
from parser import parse_feed
from store import BulkUpdateQueue
from store import Connection
from store import find_entries_by_uid
from store import stale_feeds
import logging
import time

def import_feeds(conn: Connection, *feed_urls: str) -> set[str]:
    successful, _ = _fetch_feeds(*feed_urls)
    if not len(successful):
        return set()

    feed_count = 0
    entry_count = 0
    id_url_map = {}

    with BulkUpdateQueue(conn) as bulk_q:
        for result in successful:
            feed = result.feed
            feed_count += 1
            id_url_map[feed.id] = feed.feed_url

            feed.digest = feed.computed_digest()

            bulk_q.enqueue_flex(feed)

            entry_count += len(result.entries)
            for entry in result.entries:
                entry.feed_id = result.feed.id
                entry.digest = entry.computed_digest()

                bulk_q.enqueue_flex(entry)

    for id in bulk_q.pop_written_ids():
        id_url_map.pop(id, None)

    logging.debug(f"Wrote {bulk_q.written_count} objects; {feed_count}/{entry_count} feeds/entries")

    return id_url_map.values()

def refresh_feeds(conn: Connection, freshness_seconds: int):
    now = time.mktime(time.localtime())
    stale_start = time.gmtime(now - freshness_seconds)

    pending_fetch = []
    fetch_batch_max = 40

    with BulkUpdateQueue(conn) as bulk_q:
        # TODO: probably good to set some sort of max limit
        for feed in stale_feeds(conn, stale_start=stale_start):
            pending_fetch.append(feed)
            if len(pending_fetch) >= fetch_batch_max:
                _freshen_stale_feed_content(conn, bulk_q, *pending_fetch)
                pending_fetch.clear()

            # Don't let it grow too large
            bulk_q.pop_written_ids()

        if pending_fetch:
            _freshen_stale_feed_content(conn, bulk_q, *pending_fetch)
            pending_fetch.clear()

def _freshen_stale_feed_content(conn: Connection, bulk_q: BulkUpdateQueue, *feeds: FeedContent):
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

            bulk_q.enqueue_flex(remote_feed)

        remote_entry_map = { entry.entry_uid:entry for entry in result.entries }
        for local_entry in find_entries_by_uid(conn, local_feed.id, *remote_entry_map.keys()):
            remote_entry = remote_entry_map[local_entry.entry_uid]
            if remote_entry.digest != local_entry.digest:
                remote_entry.feed_id = local_feed.id
                remote_entry.rev = local_entry.rev
                remote_entry.id = local_entry.id
                remote_entry.digest = remote_entry.computed_digest()

                bulk_q.enqueue_flex(remote_entry)
                entries_changed += 1
                del remote_entry_map[local_entry.entry_uid]
            else:
                del remote_entry_map[local_entry.entry_uid]

        for remote_entry in remote_entry_map.values():
            remote_entry.feed_id = local_feed.id
            remote_entry.digest = remote_entry.computed_digest()
            bulk_q.enqueue_flex(remote_entry)
            entries_changed += 1

    logging.debug(f"{feeds_changed} feeds and {entries_changed} entries updated")

def _fetch_feeds(*feed_urls: str) -> tuple[list[ParseResult], list[ParseResult]]:
    start = time.time()

    successful = []
    failed = []
    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_url = { executor.submit(parse_feed, url):url for url in feed_urls }
        for future in as_completed(future_to_url):
            url = future_to_url[future]
            try:
                result = future.result()
                if result.success():
                    successful.append(result)
                else:
                    failed.append(result)
            except Exception as e:
                logging.exception(f"Failed to load {url}", e)

    logging.debug(f"Fetched {len(feed_urls)} in {"%.2f" % (time.time() - start)}s; {len(successful)} OK, {len(failed)} failed")

    return successful, failed
