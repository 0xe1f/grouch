from common import build_key
from common import decompose_key
from datatype.flex_object import FlexObject
from datatype.user import User
from uuid import uuid4

class Folder(FlexObject):

    DOC_TYPE = "folder"

    def __init__(self, source: dict[str, str]={}):
        super().__init__(source)

    @property
    def id(self) -> str:
        return self._doc.get("id")

    @id.setter
    def id(self, val: str):
        self._doc["id"] = val

    @property
    def title(self) -> str:
        return self._doc.get("title")

    @title.setter
    def title(self, val: str):
        self._doc["title"] = val

    @property
    def user_id(self) -> int:
        return self._doc.get("user_id")

    @user_id.setter
    def user_id(self, val: int):
        self._doc["user_id"] = val

    def build_key(self) -> str|None:
        return build_key(self.doc_type, self.user_id,  uuid4().hex)

    @staticmethod
    def extract_owner_id(obj_id: str) -> str|None:
        doc_type, parts = decompose_key(obj_id)
        if doc_type != __class__.DOC_TYPE:
            return None
        if len(parts) != 2:
            return None
        return build_key(User.DOC_TYPE, parts[0])
