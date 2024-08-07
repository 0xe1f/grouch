from datatype.feed_content import FeedContent
from datatype.subscription import Subscription
from web.ext_type.json_object import JsonObject

class PublicSub(JsonObject):

    def __init__(self, sub: Subscription|None=None, feed: FeedContent|None=None, source: dict={}):
        super().__init__(source)
        if sub:
            self.set_prop("id", sub.id)
            self.set_prop("title", sub.title)
            self.set_prop("unread", sub.unread_count)
            self.set_prop("parent", sub.folder_id)
        if feed:
            self.set_prop("faviconUrl", feed.favicon_url)
            self.set_prop("link", feed.site_url)

    @property
    def id(self) -> str:
        return self._doc.get("id")

    @property
    def link(self) -> str:
        return self._doc.get("link")

    @property
    def title(self) -> str:
        return self._doc.get("title")

    @property
    def unread_count(self) -> int:
        return self._doc.get("unread")

    @property
    def favicon_url(self) -> str:
        return self._doc.get("faviconUrl")

    @property
    def folder_id(self) -> str:
        return self._doc.get("parent")
