class SubFolder:

    def __init__(self, id: str=None, title: str=None):
        self._parent_id = None
        self._id = id
        self._title = title

    @property
    def id(self) -> str:
        return self._id

    @id.setter
    def id(self, val: str):
        self._id = val

    @property
    def title(self) -> str:
        return self._title

    @title.setter
    def title(self, val: str):
        self._title = val

    @property
    def parent_id(self) -> str:
        return self._parent_id

    @parent_id.setter
    def parent_id(self, val: str):
        self._parent_id = val
