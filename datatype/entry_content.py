import hashlib
import json

class EntryContent:

    def __init__(self, id: str, doc):
        self.__dict__.update(**doc)
        self.computed_digest = None
        self.id = id
        self.doc = doc

    def digest(self):
        if not self.computed_digest:
            m = hashlib.md5()
            m.update(json.dumps(self.doc).encode())
            self.computed_digest = m.hexdigest()

        return self.computed_digest
