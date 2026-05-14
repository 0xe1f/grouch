#!/usr/bin/env python3

# Copyright (C) 2024 Akop Karapetyan
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from os.path import abspath
from os.path import dirname
from os.path import exists
from os.path import join
from urllib.parse import quote_plus
import couchdb
import logging
import time
import tomllib

POLL_INTERVAL_SECS = 15

def main():
    logging.basicConfig(level=logging.INFO)
    log = logging.getLogger(__name__)

    config_path = "config.toml"
    if not exists(config_path):
        script_dir = dirname(abspath(__file__))
        config_path = join(script_dir, "config.toml")

    with open(config_path, "rb") as f:
        config = tomllib.load(f)

    db_name = config["DATABASE_NAME"]
    username = config["DATABASE_USERNAME"]
    password = config["DATABASE_PASSWORD"]
    host = config["DATABASE_HOST"]
    port = int(config.get("DATABASE_PORT") or 5984)
    scheme = "https" if port == 443 else "http"

    server = couchdb.Server(f"{scheme}://{quote_plus(username)}:{quote_plus(password)}@{host}:{port}/")
    db = server[db_name]

    log.info(f"Triggering compaction on '{db_name}'...")
    db.resource.post_json("_compact", headers={"Content-Type": "application/json"})

    log.info("Polling for compaction to complete...")
    while True:
        _, _, info = db.resource.get_json()
        if not info.get("compact_running", False):
            break
        log.info("Compaction still running, waiting...")
        time.sleep(POLL_INTERVAL_SECS)

    log.info("Compaction complete.")

if __name__ == "__main__":
    main()
