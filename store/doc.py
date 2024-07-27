from common import format_iso
from datatype import EntryContent
from datatype import FeedContent
from parser import ParseResult
from store import Connection
from time import gmtime

def store_doc(conn: Connection, result: ParseResult) -> bool:
    # FIXME!! compute digest of all entries to avoid reading them one by one
    # FIXME!! bulk fetch?
    changed = False
    for entry in result.entries:
        changed = store_entry(conn, entry, result.feed) or changed
    changed = store_feed(conn, result.feed, changed) or changed

    return changed

def store_feed(conn: Connection, feed: FeedContent, force: bool=False) -> bool:
    item_id = feed_id(feed)
    if item_id in conn.db:
        stored = conn.db[item_id]
    else:
        stored = {
            "doc_type": "feed",
            "digest": "",
        }

    digest = feed.digest()
    if stored["digest"] == digest and not force:
        print("* digests identical")
        return False

    metadata = {
        "digest": digest,
        "updated": format_iso(gmtime()),
    }
    conn.db[item_id] = stored | { "content": feed.doc } | metadata

    return True

def store_entry(conn: Connection, entry: EntryContent, feed: FeedContent, force: bool=False) -> bool:
    item_id = entry_id(entry, feed)
    if item_id in conn.db:
        stored = conn.db[item_id]
    else:
        stored = {
            "feed_id": feed_id(feed),
            "doc_type": "entry",
            "digest": "",
        }

    digest = entry.digest()
    if stored["digest"] == digest and not force:
        print("> digests identical")
        return False

    metadata = {
        "digest": digest,
        "updated": format_iso(gmtime()),
    }
    conn.db[item_id] = stored | { "content": entry.doc } | metadata

    return True

def entry_id(entry: EntryContent, feed: FeedContent) -> str:
    return f"entry::{feed.id}::{entry.id}"

def feed_id(feed: FeedContent) -> str:
    return f"feed::{feed.id}"
