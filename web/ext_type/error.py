from web.ext_type.json_object import JsonObject
import http

class Error(JsonObject):

    def __init__(self, message: str):
        super().__init__({})
        self.set_prop("message", message)

    @property
    def message(self) -> str:
        return self.get_prop("message")

    def as_dict(self):
        return super().as_dict(), http.HTTPStatus.BAD_REQUEST
