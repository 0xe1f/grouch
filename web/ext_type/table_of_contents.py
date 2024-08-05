from web.ext_type.json_object import JsonObject
from web.ext_type.public_sub import PublicSub

class TableOfContents(JsonObject):

    def __init__(self, source: dict={}, subs: list[PublicSub]=[]):
        super().__init__(source)
        self.set_prop("subscriptions", [sub.as_dict() for sub in subs])
        self.set_prop("folders", [])
        self.set_prop("tags", [])

    @property
    def subscriptions(self) -> list[PublicSub]:
        return [PublicSub(sub) for sub in self._doc.get("subscriptions")]
