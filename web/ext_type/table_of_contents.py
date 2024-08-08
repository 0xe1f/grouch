from web.ext_type.json_object import JsonObject
from web.ext_type.folder import Folder as PubFolder
from web.ext_type.public_sub import PublicSub
from web.ext_type.tag import Tag

class TableOfContents(JsonObject):

    def __init__(self, source: dict={}, subs: list[PublicSub]=[], folders: list[PubFolder]=[], tags: list[str]=[]):
        super().__init__(source)
        self.set_prop("subscriptions", [sub.as_dict() for sub in subs])
        self.set_prop("folders", [folder.as_dict() for folder in folders])
        self.set_prop("tags", [tag.as_dict() for tag in tags])

    @property
    def subscriptions(self) -> list[PublicSub]:
        return [PublicSub(sub) for sub in self._doc.get("subscriptions")]

    @property
    def subscriptions(self) -> list[PubFolder]:
        return [PubFolder(folder) for folder in self._doc.get("folders")]

    @property
    def subscriptions(self) -> list[Tag]:
        return [Tag(tag) for tag in self._doc.get("tags")]
