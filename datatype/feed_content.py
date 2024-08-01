import hashlib
import json

class FeedContent:

    def __init__(self, source: dict[str, str]={}):
        self._doc = source.copy()
        self._computed_digest = None

    @property
    def id(self) -> str:
        return self._doc.get("id")

    @id.setter
    def id(self, val: str):
        self._doc["id"] = val
        # Hash is unaffected

    @property
    def feed_url(self) -> str:
        return self._doc.get("feed_url")

    @feed_url.setter
    def feed_url(self, val: str):
        self._doc["feed_url"] = val
        self._computed_digest = None

    @property
    def title(self) -> str:
        return self._doc.get("title")

    @title.setter
    def title(self, val: str):
        self._doc["title"] = val
        self._computed_digest = None

    @property
    def description(self) -> str:
        return self._doc.get("description")

    @description.setter
    def description(self, val: str):
        self._doc["description"] = val
        self._computed_digest = None

    @property
    def favicon_url(self) -> str:
        return self._doc.get("favicon_url")

    @favicon_url.setter
    def favicon_url(self, val: str):
        self._doc["favicon_url"] = val
        self._computed_digest = None

    @property
    def site_url(self) -> str:
        return self._doc.get("site_url")

    @site_url.setter
    def site_url(self, val: str):
        self._doc["site_url"] = val
        self._computed_digest = None

    @property
    def published(self) -> str:
        return self._doc.get("published")

    @published.setter
    def published(self, val: str):
        self._doc["published"] = val
        self._computed_digest = None

    def doc(self):
        return self._doc

    def digest(self):
        if not self._computed_digest:
            # Remove identifiers
            doc = self._doc.copy()
            if "id" in doc:
                del doc["id"]

            # Compute hash
            m = hashlib.md5()
            m.update(json.dumps(doc).encode())
            self._computed_digest = m.hexdigest()

        return self._computed_digest
