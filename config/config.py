from config.database_config import DatabaseConfig

class Config:

    def __init__(self):
        self._database = None

    @property
    def database(self) -> DatabaseConfig:
        return self._database

    @database.setter
    def database(self, val: DatabaseConfig):
        self._database = val
