from web.ext_type.json_object import JsonObject

class Rename(JsonObject):

    def __init__(self, source: dict={}):
        super().__init__(source)

    @property
    def id(self) -> str:
        return self.get_prop("id")

    @property
    def title(self) -> str:
        return self.get_prop("title")
