class SubSource:

    def __init__(self, url: str=None, title: str=None):
        self._parent_id = None
        self._url = url
        self._title = title

    @property
    def title(self) -> str:
        return self._title

    @title.setter
    def title(self, val: str):
        self._title = val

    @property
    def url(self) -> str:
        return self._url

    @url.setter
    def url(self, val: str):
        self._url = val

    @property
    def parent_id(self) -> str:
        return self._parent_id

    @parent_id.setter
    def parent_id(self, val: str):
        self._parent_id = val
