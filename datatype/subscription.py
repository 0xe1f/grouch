class Subscription:

    def __init__(self):
        self._doc = {}

    @property
    def title(self) -> str:
        return self._doc.get("title")

    @title.setter
    def title(self, val: str):
        self._doc["title"] = val

    @property
    def unread_count(self) -> int:
        return self._doc.get("unread_count")

    @unread_count.setter
    def unread_count(self, val: int):
        self._doc["unread_count"] = val

    @property
    def subscribed(self):
        return self._doc.get("subscribed")

    @subscribed.setter
    def subscribed(self, val: str):
        self._doc["subscribed"] = val

    @property
    def feed_id(self):
        return self._doc.get("feed_id")

    @feed_id.setter
    def feed_id(self, val: str):
        self._doc["feed_id"] = val

    @property
    def folder_id(self):
        return self._doc.get("folder_id")

    @folder_id.setter
    def folder_id(self, val: str):
        self._doc["folder_id"] = val

    @property
    def user_id(self) -> int:
        return self._doc.get("user_id")

    @user_id.setter
    def user_id(self, val: int):
        self._doc["user_id"] = val

    def doc(self):
        return self._doc
