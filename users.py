#! /usr/bin/env python

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
