#! /usr/bin/env python3

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

from argparse import ArgumentParser
from datetime import datetime
from os.path import abspath
from os.path import dirname
from os.path import exists
from os.path import join
from dao import Database
from tasks.feeds import refresh_feeds
import logging
import dao
import tomllib

def main():
    arg_parser = ArgumentParser()
    arg_parser.add_argument(
        "-f",
        "--fresh",
        help="freshness duration, in minutes (default: REFRESH_INTERVAL_MINUTES from config)",
        required=False,
        type=int
    )

    args = arg_parser.parse_args()
    logging.basicConfig(level=logging.DEBUG)

    config_path = "config.toml"
    if not exists(config_path):
        script_dir = dirname(abspath(__file__))
        config_path = join(script_dir, "config.toml")

    with open(config_path, "rb") as file:
        config = tomllib.load(file)

    conn = dao.Connection()
    conn.connect(
        config["DATABASE_NAME"],
        config["DATABASE_USERNAME"],
        config["DATABASE_PASSWORD"],
        config["DATABASE_HOST"],
        config.get("DATABASE_PORT")
    )

    db = Database(conn.db)

    fresh_minutes = args.fresh if args.fresh is not None else config["REFRESH_INTERVAL_MINUTES"]
    print(f"{datetime.now()}: updating feeds older than {fresh_minutes} minutes")
    freshness_seconds = fresh_minutes * 60
    refresh_feeds(db, freshness_seconds)

if __name__ == "__main__":
    main()
