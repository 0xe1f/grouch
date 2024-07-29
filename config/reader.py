from config.config import Config
from config.database_config import DatabaseConfig
import yaml


def read_config(path) -> Config:
    config = Config()
    with open(path, 'r') as fd:
        conf = yaml.safe_load(fd)
        if "database" in conf:
            config.database = DatabaseConfig(**conf["database"])

    return config

