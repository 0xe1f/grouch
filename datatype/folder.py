class Folder:

    def __init__(self, source: map=None):
        if source:
            self._doc = {} | source
        else:
            self._doc = {}

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

    def doc(self):
        return self._doc
