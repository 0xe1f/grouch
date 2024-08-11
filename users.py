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
from datatype import User
from store import create_user
from store import Connection
import bcrypt
import logging

arg_parser = ArgumentParser()
arg_parser.add_argument("-u", "--username", help="user's username", required=True)
arg_parser.add_argument("-p", "--password", help="user's password", required=True)
arg_parser.add_argument("-e", "--email", help="user's email", required=True)

# FIXME!! none of these fields are validated for now

args = arg_parser.parse_args()
config = read_config("config.yaml")

conn = Connection()
conn.connect(config.database)

salt = bcrypt.gensalt()

user = User()
user.username = args.username
user.set_hashed_password(args.password, salt)
user.email_address = args.email

success = create_user(conn, user)
if not success:
    logging.warning("Cannot create user")

logging.info("User created successfully")
