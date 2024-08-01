from datatype import EntryContent
from datatype import FeedContent

class ParseResult:

    def __init__(self, url: str, error: str=None, feed: FeedContent=None, entries: list[EntryContent]=None):
        self.url = url
        self.feed = feed
        self.entries = entries
        self.error = error

    def success(self) -> bool:
        return not self.error
