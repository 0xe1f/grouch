from web.ext_type.json_object import JsonObject

class CreateFolderRequest(JsonObject):

    def __init__(self, source: dict[str, str]={}):
        super().__init__(source)

    @property
    def title(self) -> str:
        return self.get_prop("title")

class RenameRequest(JsonObject):

    def __init__(self, source: dict={}):
        super().__init__(source)

    @property
    def id(self) -> str:
        return self.get_prop("id")

    @property
    def title(self) -> str:
        return self.get_prop("title")

class SetPropertyRequest(JsonObject):

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

class SetTagsRequest(JsonObject):

    def __init__(self, source: dict[str, str]={}):
        super().__init__(source)

    @property
    def article_id(self) -> str:
        return self.get_prop("articleId")

    @property
    def tags(self) -> list[str]:
        return self.get_prop("tags")
