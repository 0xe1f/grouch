from web.ext_type.json_object import JsonObject
from web.ext_type.folder import Folder
from web.ext_type.subscription import Subscription
from web.ext_type.tag import Tag

class TableOfContents(JsonObject):

    def __init__(self, source: dict={}, subs: list[Subscription]=[], folders: list[Folder]=[], tags: list[Tag]=[]):
        super().__init__(source)
        self.set_prop("subscriptions", [sub.as_dict() for sub in subs])
        self.set_prop("folders", [folder.as_dict() for folder in folders])
        self.set_prop("tags", [tag.as_dict() for tag in tags])

    @property
    def subscriptions(self) -> list[Subscription]:
        return [Subscription(sub) for sub in self._doc.get("subscriptions")]

    @property
    def folders(self) -> list[Folder]:
        return [Folder(folder) for folder in self._doc.get("folders")]

    @property
    def subscriptions(self) -> list[str]:
        return self._doc.get("tags")
