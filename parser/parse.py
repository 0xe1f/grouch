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

from common import format_iso
from datatype import EntryContent
from datatype import FeedContent
from parser import ParseResult
from parser import sanitizer
import feedparser

_MAX_SUMMARY_LEN = 400

def parse_feed(url: str) -> ParseResult:
    doc = feedparser.parse(url)
    if not doc:
        return ParseResult(url, error="No document to parse")
    if "feed" not in doc:
        return ParseResult(url, error="Document is missing feed")
    if not doc.entries:
        return ParseResult(url, error="Document is missing entries")
    if "title" not in doc.feed:
        return ParseResult(url, error="Feed is missing a title")

    feed = create_feed_content(url, doc.feed)
    entries = [create_entry_content(entry) for entry in doc.entries]

    return ParseResult(url, feed=feed, entries=entries)

def create_feed_content(url, feed):
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
        content.published = format_iso(feed.updated_parsed)
    elif "published" in feed:
        content.published = format_iso(feed.published_parsed)
    content.digest = content.computed_digest()

    return content

def create_entry_content(entry):
    html_content = sanitizer.sanitize_html(entry.description)
    text_content = sanitizer.extract_text(html_content, max_len=_MAX_SUMMARY_LEN)

    content = EntryContent()
    content.entry_uid = entry.id
    content.title = entry.title
    if "author" in entry:
        content.author = entry.author
    content.link = entry.link
    content.text_body = html_content
    if "updated" in entry:
        content.published = format_iso(entry.updated_parsed)
    elif "published" in entry:
        content.published = format_iso(entry.published_parsed)
    content.text_summary = text_content
    content.digest = content.computed_digest()

    return content
