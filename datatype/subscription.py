from common import build_key
from common import decompose_key
from datatype.flex_object import FlexObject
from datatype.user import User

class Subscription(FlexObject):

    DOC_TYPE = "sub"

    def __init__(self, source: dict[str, str]={}):
        super().__init__(source)
        if not source:
            self.doc_type = __class__.DOC_TYPE
            self.unread_count = 0

    @property
    def title(self) -> str:
        return self.get_prop("title")

    @title.setter
    def title(self, val: str):
        self.set_prop("title", val)

    @property
    def unread_count(self) -> str:
        return self.get_prop("unread_count")

    @unread_count.setter
    def unread_count(self, val: str):
        self.set_prop("unread_count", val)

    @property
    def subscribed(self) -> str:
        return self.get_prop("subscribed")

    @subscribed.setter
    def subscribed(self, val: str):
        self.set_prop("subscribed", val)

    @property
    def feed_id(self) -> str:
        return self.get_prop("feed_id")

    @feed_id.setter
    def feed_id(self, val: str):
        self.set_prop("feed_id", val)

    @property
    def folder_id(self) -> str:
        return self.get_prop("folder_id")

    @folder_id.setter
    def folder_id(self, val: str):
        self.set_prop("folder_id", val)

    @property
    def last_synced(self) -> str:
        return self.get_prop("last_synced")

    @last_synced.setter
    def last_synced(self, val: str):
        self.set_prop("last_synced", val)

    @property
    def user_id(self) -> str:
        return self.get_prop("user_id")

    @user_id.setter
    def user_id(self, val: str):
        self.set_prop("user_id", val)

    def new_key(self) -> str|None:
        if not self.user_id:
            raise ValueError("Missing user id")
        if not self.feed_id:
            raise ValueError("Missing entry feed id")

        return build_key(self.doc_type, self.user_id, self.feed_id)

    @staticmethod
    def extract_owner_id(obj_id: str) -> str|None:
        doc_type, parts = decompose_key(obj_id)
        if doc_type != __class__.DOC_TYPE:
            return None
        if len(parts) != 2:
            return None
        return build_key(User.DOC_TYPE, parts[0])
