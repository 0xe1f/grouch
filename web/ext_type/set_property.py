from web.ext_type.json_object import JsonObject

class SetProperty(JsonObject):

    def __init__(self, source: dict[str, str]={}):
        super().__init__(source)

    @property
    def article_id(self) -> str:
        return self.get_prop("article")

    @property
    def prop_name(self) -> str:
        return self.get_prop("property")

    @property
    def is_set(self) -> bool:
        return self.get_prop("set")
