class Subscription:

    def __init__(self, source: dict | None=None):
        self._doc = (source or {}).copy()
        if source == None:
            self.unread_count = 0

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
    def unread_count(self) -> int:
        return self._doc.get("unread_count")

    @unread_count.setter
    def unread_count(self, val: int):
        self._doc["unread_count"] = val

    @property
    def subscribed(self) -> str:
        return self._doc.get("subscribed")

    @subscribed.setter
    def subscribed(self, val: str):
        self._doc["subscribed"] = val

    @property
    def feed_id(self) -> str:
        return self._doc.get("feed_id")

    @feed_id.setter
    def feed_id(self, val: str):
        self._doc["feed_id"] = val

    @property
    def folder_id(self) -> str:
        return self._doc.get("folder_id")

    @folder_id.setter
    def folder_id(self, val: str):
        self._doc["folder_id"] = val

    @property
    def last_synced(self) -> str:
        return self._doc.get("last_synced")

    @last_synced.setter
    def last_synced(self, val: str):
        self._doc["last_synced"] = val

    @property
    def user_id(self) -> str:
        return self._doc.get("user_id")

    @user_id.setter
    def user_id(self, val: str):
        self._doc["user_id"] = val

    def doc(self):
        return self._doc
