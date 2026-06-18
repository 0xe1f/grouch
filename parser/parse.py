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

from dataclasses import dataclass
from html.parser import unescape
from entity import Entry
from entity import Feed
from parser.defs import Alternative
from parser.defs import ParseResult
from parser import sanitizer
from parser import consts
import datetime
import feedparser
import logging
import requests
import time

_FEED_TYPES = [
    "application/atom+xml",
    "application/rss+xml",
]

@dataclass
class _Fetched:
    content: bytes | None = None
    headers: dict | None = None
    etag: str | None = None
    last_modified: str | None = None
    not_modified: bool = False

def _fetch_url(
    url: str,
    etag: str | None = None,
    last_modified: str | None = None,
) -> _Fetched | None:
    """Fetch raw feed bytes with a hard timeout and conditional GET support.

    feedparser has no timeout of its own, so we do the HTTP request and pass the
    body to feedparser.parse(). When etag/last_modified are supplied we send
    If-None-Match / If-Modified-Since; a 304 response yields a not-modified
    result (the caller skips re-parsing). Returns None on any request failure
    (timeout, connection error, etc.). We intentionally do not call
    raise_for_status() — feedparser's bozo/version checks already handle bad
    or error-page content.
    """
    req_headers = {}
    if etag:
        req_headers["If-None-Match"] = etag
    if last_modified:
        req_headers["If-Modified-Since"] = last_modified

    try:
        response = requests.get(
            url,
            timeout=consts.FEED_FETCH_TIMEOUT_SECS,
            headers=req_headers or None,
        )
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to fetch '{url}': {e}")
        return None

    if response.status_code == 304:
        # Server confirms our cached copy is current; echo the validators back.
        return _Fetched(etag=etag, last_modified=last_modified, not_modified=True)

    # feedparser looks up response headers by lowercase key; requests preserves
    # the server's casing (e.g. "Content-Type"), so it would otherwise miss the
    # content type and flag the feed as NonXMLContentType. Drop content-encoding
    # and content-length too: requests has already transparently decompressed
    # the body, so those headers no longer describe the bytes we hand off.
    headers = {
        k.lower(): v for k, v in response.headers.items()
        if k.lower() not in ("content-encoding", "content-length")
    }

    return _Fetched(
        content=response.content,
        headers=headers,
        etag=response.headers.get("ETag"),
        last_modified=response.headers.get("Last-Modified"),
    )

def parse_url(url: str) -> ParseResult:
    if not (fetched := _fetch_url(url)):
        logging.error(f"FeedParser returned nothing for '{url}'")
        return None

    doc = feedparser.parse(fetched.content, response_headers=fetched.headers)

    if "version" not in doc:
        if "bozo_exception" in doc:
            logging.error(f"FeedParser returned an error for '{url}': '{doc.bozo_exception}'")
        else:
            logging.error(f"FeedParser returned an error for '{url}'")
        return None

    if doc.version:
        # URL represents an actual feed
        return _parse_feed(doc, url, etag=fetched.etag, last_modified=fetched.last_modified)

    # Possibly an HTML doc? Try to extract an RSS feed
    if "feed" not in doc:
        logging.error(f"No feed content and no feed node for '{url}'")
        return None
    elif "links" not in doc.feed:
        logging.error(f"No feed content and no links node for '{url}'")
        return None

    # Extract RSS feed, and attempt to parse it
    alts = [
        Alternative(url=link["href"], title=unescape(link.get("title", link["href"])))
        for link in doc.feed.links
            if link.get("rel") == "alternate" and link.get("type") in _FEED_TYPES
    ]
    if alts:
        logging.debug(f"No feeds for '{url}', but found {len(alts)} alternatives")
        return ParseResult(url, alternatives=alts)

    logging.error(f"No feeds for '{url}'")
    return None

def parse_feed(
    url: str,
    etag: str | None = None,
    last_modified: str | None = None,
) -> ParseResult:
    fetched = _fetch_url(url, etag=etag, last_modified=last_modified)
    if fetched is None:
        logging.error(f"No document available for '{url}'")
        return ParseResult(url)

    if fetched.not_modified:
        return ParseResult(url, not_modified=True)

    doc = feedparser.parse(fetched.content, response_headers=fetched.headers)

    return _parse_feed(doc, url, etag=fetched.etag, last_modified=fetched.last_modified)

def _parse_feed(
    doc: feedparser.FeedParserDict,
    url: str,
    etag: str | None = None,
    last_modified: str | None = None,
) -> ParseResult:
    if "status" in doc and doc.status == 404:
        logging.error(f"Doc not found (404) ({url})")
        return ParseResult(url)
    elif not doc:
        logging.error(f"No document to parse ({url})")
        return ParseResult(url)
    elif "feed" not in doc:
        logging.error(f"Document is missing feed ({url})")
        return ParseResult(url)
    elif "entries" not in doc:
        logging.error(f"Document is missing entries ({url})")
        return ParseResult(url)
    elif "title" not in doc.feed:
        logging.error(f"Document is missing title ({url})")
        return ParseResult(url)

    return ParseResult(
        url,
        feed=_create_feed(url, doc.feed, etag=etag, last_modified=last_modified),
        entries=[_create_entry(entry) for entry in doc.entries],
    )

def _create_feed(
    url: str,
    feed: feedparser.FeedParserDict,
    etag: str | None = None,
    last_modified: str | None = None,
) -> Feed:
    content = Feed()
    content.feed_url = url
    content.title = (feed.title or "")[:consts.MAX_TITLE_LEN]
    description = None
    if "subtitle" in feed:
        description = feed.subtitle
    elif "description" in feed:
        description = feed.description
    if description:
        content.description = description[:consts.MAX_FEED_DESCRIPTION_LEN]
    # TODO content.favicon_url = None
    content.site_url = feed.link
    if "updated" in feed:
        content.published = _utc_struct_as_timestamp(feed.updated_parsed)
    elif "published" in feed:
        content.published = _utc_struct_as_timestamp(feed.published_parsed)
    content.etag = etag
    content.last_modified = last_modified
    content.digest = content.computed_digest()

    return content

def _create_entry(entry: feedparser.FeedParserDict) -> Entry:
    body = _entry_body(entry)
    html_content = sanitizer.sanitize_html(body)
    text_content = sanitizer.extract_text(html_content, max_len=consts.MAX_SUMMARY_LEN)

    content = Entry()
    content.entry_uid = entry.id
    content.title = entry.title
    if "author" in entry:
        content.author = entry.author
    content.link = entry.link
    content.text_body = html_content
    if "updated" in entry:
        content.published = _utc_struct_as_timestamp(entry.updated_parsed)
    elif "published" in entry:
        content.published = _utc_struct_as_timestamp(entry.published_parsed)
    content.text_summary = text_content
    content.digest = content.computed_digest()

    return content

def _entry_body(entry: feedparser.FeedParserDict) -> str:
    if "content" in entry and len(entry.content):
        if (content := entry.content[0]) and "value" in content:
            return content.value
    elif "summary_detail" in entry:
        if (summary_detail := entry.summary_detail) and "value" in summary_detail:
            return summary_detail.value
    elif "description" in entry:
        return entry.description

    return ""

def _utc_struct_as_timestamp(t: time.struct_time) -> int:
    yr, mo, dy, hr, min, sec, *_ = t
    dt = datetime.datetime(yr, mo, dy, hr, min, sec, tzinfo=datetime.UTC)
    return dt.timestamp()
