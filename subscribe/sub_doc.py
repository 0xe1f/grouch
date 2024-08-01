class SubDoc:

    def __init__(self, sub_folders: list, sub_sources: list):
        self._sub_folders = sub_folders
        self._sub_sources = sub_sources

    @property
    def sub_folders(self) -> list:
        return self._sub_folders

    @property
    def sub_sources(self) -> list:
        return self._sub_sources
