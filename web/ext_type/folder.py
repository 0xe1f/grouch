from web.ext_type.json_object import JsonObject

class Folder(JsonObject):

    def __init__(self, source: dict={}):
        super().__init__(source)
        self.set_prop("id", "feh")
        self.set_prop("title", "Feh")

    @property
    def id(self) -> str:
        return self._doc.get("id")

    @property
    def title(self) -> str:
        return self._doc.get("title")
