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
from entity import Feed
from parser import ParseResult
from parser import parse_feed
from dao import BulkUpdateQueue
from dao import Database
import datetime
import logging
import time

def import_feeds(
    bulk_q: BulkUpdateQueue,
    *feed_urls: str,
) -> set[str]:
    # Fresh imports have no cached validators yet — fetch unconditionally.
    successful, _, _ = _fetch_feeds(*[(url, None, None) for url in feed_urls])
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
    dao: Database,
    freshness_seconds: int,
):
    now = datetime.datetime.now()
    stale_start = now - datetime.timedelta(seconds=freshness_seconds)

    pending_fetch = []
    fetch_batch_max = 40

    with dao.new_q() as bulk_q:
        # TODO: probably good to set some sort of max limit
        for feed in dao.feeds.iter_updated_before(stale_start=stale_start.timestamp()):
            pending_fetch.append(feed)
            if len(pending_fetch) >= fetch_batch_max:
                _freshen_stale_feed(dao, bulk_q, *pending_fetch)
                pending_fetch.clear()

        if pending_fetch:
            _freshen_stale_feed(dao, bulk_q, *pending_fetch)
            pending_fetch.clear()

def _freshen_stale_feed(
    dao: Database,
    bulk_q: BulkUpdateQueue,
    *feeds: Feed,
):
    local_feed_map = { feed.feed_url:feed for feed in feeds }

    feeds_changed = 0
    entries_changed = 0
    specs = [
        (feed.feed_url, feed.etag, feed.last_modified)
        for feed in local_feed_map.values()
    ]
    successful, failed, not_modified = _fetch_feeds(*specs)

    # Log the outcome for every feed, regardless of result.
    for result in not_modified:
        logging.info(f"Feed unchanged (304 Not Modified): {result.url}")
    for result in failed:
        logging.info(f"Feed fetch failed (no content): {result.url}")

    for result in successful:
        remote_feed = result.feed
        local_feed = local_feed_map[remote_feed.feed_url]

        feed_meta_changed = remote_feed.digest != local_feed.digest
        # Persist refreshed validators even when content is unchanged, otherwise
        # the conditional GET never becomes effective for a stable feed.
        validators_changed = (
            remote_feed.etag != local_feed.etag
            or remote_feed.last_modified != local_feed.last_modified
        )
        if feed_meta_changed or validators_changed:
            feeds_changed += feed_meta_changed
            remote_feed.rev = local_feed.rev
            remote_feed.id = local_feed.id
            remote_feed.digest = remote_feed.computed_digest()

            bulk_q.enqueue(remote_feed)

        feed_entries_changed = 0
        remote_entry_map = { entry.entry_uid:entry for entry in result.entries }
        for local_entry in dao.entries.iter_by_uid(local_feed.id, *remote_entry_map.keys()):
            remote_entry = remote_entry_map[local_entry.entry_uid]
            if remote_entry.digest != local_entry.digest:
                remote_entry.feed_id = local_feed.id
                remote_entry.rev = local_entry.rev
                remote_entry.id = local_entry.id
                remote_entry.digest = remote_entry.computed_digest()

                bulk_q.enqueue(remote_entry)
                feed_entries_changed += 1
                del remote_entry_map[local_entry.entry_uid]
            else:
                del remote_entry_map[local_entry.entry_uid]

        for remote_entry in remote_entry_map.values():
            remote_entry.feed_id = local_feed.id
            remote_entry.digest = remote_entry.computed_digest()
            bulk_q.enqueue(remote_entry)
            feed_entries_changed += 1

        entries_changed += feed_entries_changed
        if feed_meta_changed or feed_entries_changed:
            logging.info(
                f"Feed updated: {result.url} "
                f"(metadata={'changed' if feed_meta_changed else 'same'}, "
                f"+{feed_entries_changed} entries)"
            )
        else:
            logging.info(f"Feed unchanged (200 OK, same content): {result.url}")

    logging.info(f"{feeds_changed} feeds and {entries_changed} entries updated")

def _fetch_feeds(
    *specs: tuple[str, str | None, str | None],
) -> tuple[list[ParseResult], list[ParseResult], list[ParseResult]]:
    """Fetch feeds in parallel.

    Each spec is (url, etag, last_modified); the latter two enable a conditional
    GET. Returns (successful, failed, not_modified) lists of ParseResult.
    """
    start = time.time()

    successful = []
    failed = []
    not_modified = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_url = {
            executor.submit(parse_feed, url, etag, last_modified): url
            for (url, etag, last_modified) in specs
        }
        for future in as_completed(future_to_url):
            url = future_to_url[future]
            try:
                result = future.result()
                if result.not_modified:
                    not_modified.append(result)
                elif result.feed:
                    successful.append(result)
                else:
                    failed.append(result)
            except Exception:
                logging.exception(f"Failed to load {url}")

    logging.info(
        f"Fetched {len(specs)} in {"%.2f" % (time.time() - start)}s; "
        f"{len(successful)} OK, {len(not_modified)} unchanged (304), {len(failed)} failed"
    )

    return successful, failed, not_modified
