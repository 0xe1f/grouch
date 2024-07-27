from common import format_iso
from datatype import EntryContent
from datatype import FeedContent
from parser import ParseResult
import feedparser

def parse_feed(url: str) -> ParseResult:
    doc = feedparser.parse(url)
    if not doc:
        raise ValueError("No document to parse")
    if "feed" not in doc:
        raise ValueError("Document is missing feed")
    if not doc.entries:
        raise ValueError("Document is missing entries")
    if "title" not in doc.feed:
        raise ValueError("Feed is missing a title")

    feed = create_feed_content(url, doc.feed)
    entries = [create_entry_content(entry) for entry in doc.entries]

    return ParseResult(feed, entries)

def create_feed_content(url, feed):
    doc = {}
    doc["url"] = url
    doc["title"] = feed.title
    if "subtitle" in feed:
        doc["description"] = feed.subtitle
    elif "description" in feed:
        doc["description"] = feed.description
    # doc.fav_icon = None
    doc["site_url"] = feed.link
    if "updated" in feed:
        doc["published"] = format_iso(feed.updated_parsed)
    elif "published" in feed:
        doc["published"] = format_iso(feed.published_parsed)

    return FeedContent(url, doc)

def create_entry_content(entry):
    doc = {}
    doc["title"] = entry.title
    if "author" in entry:
        doc["author"] = entry.author
    doc["link"] = entry.link
    doc["content"] = entry.description
    if "updated" in entry:
        doc["published"] = format_iso(entry.updated_parsed)
    elif "published" in entry:
        doc["published"] = format_iso(entry.published_parsed)
    # TODO: generate own
    doc["summary"] = "abc123"

    return EntryContent(entry.id, doc)
