from datatype.feed_content import FeedContent
from datatype.subscription import Subscription

class PublicSub:

    def __init__(self, sub: Subscription, feed: FeedContent):
        self._doc = {}
        self.id = sub.id
        self.link = feed.site_url
        self.title = sub.title
        self.unread_count = sub.unread_count
        self.favicon_url = feed.favicon_url
        self.folder_id = sub.folder_id

    @property
    def id(self) -> str:
        return self._doc.get("id")

    @id.setter
    def id(self, val: str):
        self._doc["id"] = val

    @property
    def link(self) -> str:
        return self._doc.get("link")

    @link.setter
    def link(self, val: str):
        self._doc["link"] = val

    @property
    def title(self) -> str:
        return self._doc.get("title")

    @title.setter
    def title(self, val: str):
        self._doc["title"] = val

    @property
    def unread_count(self) -> int:
        return self._doc.get("unread")

    @unread_count.setter
    def unread_count(self, val: int):
        self._doc["unread"] = val

    @property
    def favicon_url(self) -> str:
        return self._doc.get("faviconUrl")

    @favicon_url.setter
    def favicon_url(self, val: str):
        self._doc["faviconUrl"] = val

    @property
    def folder_id(self) -> str:
        return self._doc.get("parent")

    @folder_id.setter
    def folder_id(self, val: str):
        self._doc["parent"] = val

    def doc(self):
        return self._doc
