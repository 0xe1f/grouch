class JsonObject:

    def __init__(self, source: dict={}):
        self._doc = source.copy()

    def get_prop(self, name: str) -> object:
        return self._doc.get(name)

    def set_prop(self, name: str, val: object):
        self._doc[name] = val

    def __bool__(self):
        return not not self._doc

    def as_dict(self):
        return self._doc
