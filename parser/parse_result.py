from datatype import EntryContent
from datatype import FeedContent

class ParseResult:

    def __init__(self, url: str, error: str=None, feed: FeedContent=None, entries: list[EntryContent]=None):
        self._url = url
        self._feed = feed
        self._entries = entries
        self._error = error

    @property
    def url(self) -> str:
        return self._url

    @property
    def feed(self) -> FeedContent|None:
        return self._feed

    @property
    def entries(self) -> list[EntryContent]|None:
        return self._entries

    @property
    def error(self) -> str|None:
        return self._error

    def success(self) -> bool:
        return not self.error
