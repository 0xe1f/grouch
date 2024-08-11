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
from config import read_config
from tasks import sync_subs
import logging
import store

arg_parser = ArgumentParser()
arg_parser.add_argument("-u", "--username", help="username of subscriber", required=True)

args = arg_parser.parse_args()
config = read_config("config.yaml")
logging.basicConfig(level=logging.DEBUG)

conn = store.Connection()
conn.connect(config.database)

def main():
    user_id = store.find_user_id(conn, args.username)
    if not user_id:
        raise ValueError(f"User with username {args.username} not found")
    sync_subs(conn, user_id)

main()
