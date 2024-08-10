from common import build_key
from common import decompose_key
from datatype.flex_object import FlexObject
from datatype.user import User

class Article(FlexObject):

    PROP_UNREAD = "unread"
    PROP_LIKED = "like"
    PROP_STARRED = "star"

    DOC_TYPE = "article"

    def __init__(self, source: dict[str, str]={}):
        super().__init__(source)
        if not source:
            self.doc_type = Article.DOC_TYPE
        if self.tags == None:
            self.tags = []
        if self.props == None:
            self.props = []

    @property
    def user_id(self) -> str:
        return self.get_prop("user_id")

    @user_id.setter
    def user_id(self, val: str):
        self.set_prop("user_id", val)

    @property
    def entry_id(self) -> str:
        return self.get_prop("entry_id")

    @entry_id.setter
    def entry_id(self, val: str):
        self.set_prop("entry_id", val)

    @property
    def folder_id(self) -> str:
        return self.get_prop("folder_id")

    @folder_id.setter
    def folder_id(self, val: str):
        self.set_prop("folder_id", val)

    @property
    def subscription_id(self) -> str:
        return self.get_prop("subscription_id")

    @subscription_id.setter
    def subscription_id(self, val: str):
        self.set_prop("subscription_id", val)

    @property
    def tags(self) -> list[str]:
        return self.get_prop("tags")

    @tags.setter
    def tags(self, val: list[str]):
        self.set_prop("tags", val)

    @property
    def props(self) -> list[str]:
        return self.get_prop("props")

    @props.setter
    def props(self, val: list[str]):
        self.set_prop("props", val)

    def toggle_prop(self, name: str, is_set: bool|None=None):
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
        return self.get_prop("published")

    @published.setter
    def published(self, val: str):
        self.set_prop("published", val)

    @property
    def synced(self) -> str:
        return self.get_prop("synced")

    @synced.setter
    def synced(self, val: str):
        self.set_prop("synced", val)

    def new_key(self) -> str|None:
        if not self.user_id:
            raise ValueError("Missing user id")
        if not self.entry_id:
            raise ValueError("Missing entry id")

        return build_key(self.doc_type, self.user_id, self.entry_id)

    @staticmethod
    def extract_owner_id(obj_id: str) -> str|None:
        doc_type, parts = decompose_key(obj_id)
        if doc_type != __class__.DOC_TYPE:
            return None
        if len(parts) != 3:
            return None
        return build_key(User.DOC_TYPE, parts[0])
