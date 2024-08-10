from web.ext_type.json_object import JsonObject

class Tag(JsonObject):

    def __init__(self, tag: str|None=None, source: dict={}):
        super().__init__(source)
        if tag:
            self.set_prop("title", tag)

    @property
    def title(self) -> str:
        return self._doc.get("title")
