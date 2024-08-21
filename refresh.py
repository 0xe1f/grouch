#! /usr/bin/env python

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
from tasks import refresh_feeds
import logging
import dao
import tomllib

arg_parser = ArgumentParser()
arg_parser.add_argument(
    "-f",
    "--fresh",
    help="freshness duration, in minutes",
    required=True,
    type=int
)

args = arg_parser.parse_args()
logging.basicConfig(level=logging.DEBUG)

with open("config.toml", "rb") as file:
    config = tomllib.load(file)

conn = dao.Connection()
conn.connect(
    config["DATABASE_NAME"],
    config["DATABASE_USERNAME"],
    config["DATABASE_PASSWORD"],
    config["DATABASE_HOST"],
    config.get("DATABASE_PORT")
)

def main():
    freshness_seconds = args.fresh * 60
    refresh_feeds(conn, freshness_seconds)

main()
