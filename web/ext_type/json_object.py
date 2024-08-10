class JsonObject:

    def __init__(self, source: dict={}):
        self._doc = source.copy()

    def get_prop(self, name: str, default: object=None) -> object:
        return self._doc.get(name, default)

    def set_prop(self, name: str, val: object):
        if val != None:
            self._doc[name] = val
        else:
            # Delete null values
            self._doc.pop(name, None)

    def __bool__(self):
        return not not self._doc

    def as_dict(self):
        return self._doc
