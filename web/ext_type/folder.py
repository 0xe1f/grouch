from web.ext_type.json_object import JsonObject
import datatype

class Folder(JsonObject):

    def __init__(self, folder: datatype.Folder|None):
        super().__init__()
        if folder:
            self.set_prop("id", folder.id)
            self.set_prop("title", folder.title)

    @property
    def id(self) -> str:
        return self._doc.get("id")

    @property
    def title(self) -> str:
        return self._doc.get("title")
