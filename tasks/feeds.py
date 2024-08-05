from concurrent.futures import as_completed
from concurrent.futures import ThreadPoolExecutor
from datatype import FeedContent
from datatype import EntryContent
from parser import ParseResult
from parser import parse_feed
from store import BulkUpdateQueue
from store import Connection
from store import enqueue_entries
from store import enqueue_feeds
from store import find_entries_by_uid
from store import stale_feeds
import logging
import time

def import_feeds(conn: Connection, *feed_urls: str) -> set[str]:
    successful, _ = _fetch_feeds(*feed_urls)
    if not len(successful):
        return set()

    bulk_q = BulkUpdateQueue(conn)

    feeds_to_create = [parse_result.feed for parse_result in successful]
    enqueue_feeds(bulk_q, *feeds_to_create)

    feed_count = 0
    entry_count = 0
    for parse_result in successful:
        feed_count += 1
        entry_count += len(parse_result.entries)
        for entry in parse_result.entries:
            entry.feed_id = parse_result.feed.id
            enqueue_entries(bulk_q, entry)
    bulk_q.flush()

    feeds_written = 0
    entries_written = 0
    urls_imported = set()
    for item in bulk_q.successful_items():
        if isinstance(item, EntryContent):
            entries_written += 1
        elif isinstance(item, FeedContent):
            feeds_written += 1
            urls_imported.add(item.feed_url)

    logging.debug(f"Wrote {feeds_written}/{feed_count} feeds; {entries_written}/{entry_count} entries")

    return urls_imported

def refresh_feeds(conn: Connection, freshness_seconds: int):
    now = time.mktime(time.localtime())
    stale_start = time.gmtime(now - freshness_seconds)

    bulk_q = BulkUpdateQueue(conn)
    pending_fetch = []
    fetch_batch_max = 40
    # TODO: probably good to set some sort of max limit
    for feed in stale_feeds(conn, stale_start=stale_start):
        pending_fetch.append(feed)
        if len(pending_fetch) >= fetch_batch_max:
            _freshen_stale_feed_content(conn, bulk_q, *pending_fetch)
            pending_fetch.clear()

    if pending_fetch:
        _freshen_stale_feed_content(conn, bulk_q, *pending_fetch)
        pending_fetch.clear()

    bulk_q.flush()

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
            enqueue_feeds(bulk_q, remote_feed)

        remote_entry_map = { entry.entry_uid:entry for entry in result.entries }
        for local_entry in find_entries_by_uid(conn, local_feed.id, *remote_entry_map.keys()):
            remote_entry = remote_entry_map[local_entry.entry_uid]
            if remote_entry.digest != local_entry.digest:
                remote_entry.feed_id = local_feed.id
                remote_entry.rev = local_entry.rev
                enqueue_entries(bulk_q, remote_entry)
                entries_changed += 1
                del remote_entry_map[local_entry.entry_uid]
            else:
                del remote_entry_map[local_entry.entry_uid]

        new_entries = []
        for remote_entry in remote_entry_map.values():
            remote_entry.feed_id = local_feed.id
            new_entries.append(remote_entry)
        enqueue_entries(bulk_q, *new_entries)

    logging.debug(f"{feeds_changed} feeds and {entries_changed} entries updated, {len(new_entries)} new entries")

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
