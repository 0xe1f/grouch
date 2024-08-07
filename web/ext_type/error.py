from web.ext_type.json_object import JsonObject

class Error(JsonObject):

    def __init__(self, message: str):
        super().__init__({})
        self.set_prop("message", message)

    @property
    def message(self) -> str:
        return self.get_prop("message")
