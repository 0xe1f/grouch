import hashlib
import json

class EntryContent:

    def __init__(self, source: dict[str, str]={}):
        self._doc = source.copy()
        self.computed_digest = None

    @property
    def id(self) -> str:
        return self._doc.get("id")

    @id.setter
    def id(self, val: str):
        self._doc["id"] = val

    @property
    def feed_id(self) -> str:
        return self._doc.get("feed_id")

    @feed_id.setter
    def feed_id(self, val: str):
        self._doc["feed_id"] = val

    @property
    def entry_uid(self) -> str:
        return self._doc.get("entry_uid")

    @entry_uid.setter
    def entry_uid(self, val: str):
        self._doc["entry_uid"] = val
        self.computed_digest = None

    @property
    def title(self) -> str:
        return self._doc.get("title")

    @title.setter
    def title(self, val: str):
        self._doc["title"] = val
        self.computed_digest = None

    @property
    def author(self) -> str:
        return self._doc.get("author")

    @author.setter
    def author(self, val: str):
        self._doc["author"] = val
        self.computed_digest = None

    @property
    def link(self) -> str:
        return self._doc.get("link")

    @link.setter
    def link(self, val: str):
        self._doc["link"] = val
        self.computed_digest = None

    @property
    def text_body(self) -> str:
        return self._doc.get("text_body")

    @text_body.setter
    def text_body(self, val: str):
        self._doc["text_body"] = val
        self.computed_digest = None

    @property
    def text_summary(self) -> str:
        return self._doc.get("text_summary")

    @text_summary.setter
    def text_summary(self, val: str):
        self._doc["text_summary"] = val
        self.computed_digest = None

    @property
    def published(self) -> str:
        return self._doc.get("published")

    @published.setter
    def published(self, val: str):
        self._doc["published"] = val
        self.computed_digest = None

    def doc(self):
        return self._doc

    def digest(self):
        if not self.computed_digest:
            m = hashlib.md5()
            doc = self._doc.copy()
            if "feed_id" in doc:
                del doc["feed_id"]
            if "id" in doc:
                del doc["id"]

            m.update(json.dumps(doc).encode())
            self.computed_digest = m.hexdigest()

        return self.computed_digest
