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

from datatype import EntryContent
from datatype import FeedContent
from parser import ParseResult
from parser import sanitizer
import datetime
import feedparser
import logging
import time

_MAX_SUMMARY_LEN = 400
_FEED_TYPES = [
    "application/atom+xml",
    "application/rss+xml",
]

def parse_url(url: str) -> ParseResult:
    if not (doc := feedparser.parse(url)):
        logging.error(f"FeedParser returned nothing for '{url}'")
        return None

    if "version" not in doc:
        if "bozo_exception" in doc:
            logging.error(f"FeedParser returned an error for '{url}': '{doc.bozo_exception}'")
        else:
            logging.error(f"FeedParser returned an error for '{url}'")
        return None

    if doc.version:
        # URL represents an actual feed
        return _parse_feed(doc, url)

    # Possibly an HTML doc? Try to extract an RSS feed
    if "feed" not in doc:
        logging.error(f"No feed content and no feed node for '{url}'")
        return None
    elif "links" not in doc.feed:
        logging.error(f"No feed content and no links node for '{url}'")
        return None

    # Extract RSS feed, and attempt to parse it
    if (alt_urls := [link["href"] for link in doc.feed.links if link.get("rel") == "alternate" and link.get("type") in _FEED_TYPES]):
        logging.debug(f"No feeds for '{url}', but found {len(alt_urls)} alternatives")
        return ParseResult(url, alts=alt_urls)

    logging.error(f"No feeds for '{url}'")
    return None

def parse_feed(url: str) -> ParseResult:
    if not (doc := feedparser.parse(url)):
        logging.error(f"No document available for '{url}'")
        return None

    return _parse_feed(doc, url)

def _parse_feed(doc: feedparser.FeedParserDict, url: str) -> ParseResult:
    if not doc:
        logging.error(f"No document to parse ({url})")
    if "feed" not in doc:
        logging.error(f"Document is missing feed ({url})")
    if not doc.entries:
        logging.error(f"Document is missing entries ({url})")
    if "title" not in doc.feed:
        logging.error(f"Document is missing title ({url})")

    feed = _create_feed_content(url, doc.feed)
    entries = [_create_entry_content(entry) for entry in doc.entries]
    return ParseResult(url, feed=feed, entries=entries)

def _create_feed_content(url: str, feed: feedparser.FeedParserDict) -> FeedContent:
    content = FeedContent()
    content.feed_url = url
    content.title = feed.title
    if "subtitle" in feed:
        content.description = feed.subtitle
    elif "description" in feed:
        content.description = feed.description
    # TODO content.favicon_url = None
    content.site_url = feed.link
    if "updated" in feed:
        content.published = _utc_struct_as_timestamp(feed.updated_parsed)
    elif "published" in feed:
        content.published = _utc_struct_as_timestamp(feed.published_parsed)
    content.digest = content.computed_digest()

    return content

def _create_entry_content(entry: feedparser.FeedParserDict) -> EntryContent:
    body = _entry_body(entry)
    html_content = sanitizer.sanitize_html(body)
    text_content = sanitizer.extract_text(html_content, max_len=_MAX_SUMMARY_LEN)

    content = EntryContent()
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

    return entry.description

def _utc_struct_as_timestamp(t: time.struct_time) -> int:
    yr, mo, dy, hr, min, sec, *_ = t
    dt = datetime.datetime(yr, mo, dy, hr, min, sec, tzinfo=datetime.UTC)
    return dt.timestamp()
