import os
import tomllib
from os.path import abspath, dirname, exists, join


def load_config() -> dict:
    config_path = "config.toml"
    if not exists(config_path):
        config_path = join(dirname(abspath(__file__)), "..", "config.toml")
    with open(config_path, "rb") as f:
        config = tomllib.load(f)
    prefix = "GROUCH_"
    for key, value in os.environ.items():
        if key.startswith(prefix):
            config[key[len(prefix):]] = value
    return config
