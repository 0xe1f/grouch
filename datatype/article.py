
class Article:

    PROP_UNREAD = "unread"
    PROP_LIKED = "liked"

    def __init__(self, source: dict[str, str]={}):
        self._doc = source.copy()
        if self.tags == None:
            self.tags = []
        if self.props == None:
            self.props = []

    @property
    def id(self) -> str:
        return self._doc.get("id")

    @id.setter
    def id(self, val: str):
        self._doc["id"] = val

    @property
    def user_id(self) -> str:
        return self._doc.get("user_id")

    @user_id.setter
    def user_id(self, val: str):
        self._doc["user_id"] = val

    @property
    def entry_id(self) -> str:
        return self._doc.get("entry_id")

    @entry_id.setter
    def entry_id(self, val: str):
        self._doc["entry_id"] = val

    @property
    def subscription_id(self) -> str:
        return self._doc.get("subscription_id")

    @subscription_id.setter
    def subscription_id(self, val: str):
        self._doc["subscription_id"] = val

    @property
    def tags(self) -> list[str]:
        return self._doc.get("tags")

    @tags.setter
    def tags(self, val: list[str]):
        self._doc["tags"] = val

    @property
    def props(self) -> list[str]:
        return self._doc.get("props")

    @props.setter
    def props(self, val: list[str]):
        self._doc["props"] = val

    def toggle_prop(self, name: str, is_set: bool | None):
        if is_set == None:
            if name in self.props:
                self.props.remove(name)
            else:
                self.props.append(name)
        elif is_set and name not in self.props:
            self.props.append(name)
        elif not is_set and name in self.props:
            self.props.remove(name)

    @property
    def published(self) -> str:
        return self._doc.get("published")

    @published.setter
    def published(self, val: str):
        self._doc["published"] = val

    @property
    def synced(self) -> str:
        return self._doc.get("synced")

    @synced.setter
    def synced(self, val: str):
        self._doc["synced"] = val

    def doc(self):
        return self._doc
