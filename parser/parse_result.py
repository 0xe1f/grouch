from datatype import EntryContent
from datatype import FeedContent

class ParseResult:

    def __init__(self, feed: FeedContent, entries: list[EntryContent]):
        self.feed = feed
        self.entries = entries
