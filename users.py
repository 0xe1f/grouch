#! /usr/bin/env python

from argparse import ArgumentParser
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

conn = Connection('reader')
conn.connect("admin", "password", "localhost", 5984)

# FIXME!! check for uniqueness here before proceeding

salt = bcrypt.gensalt()

user = User()
user.username = args.username
user.set_hashed_password(args.password, salt)
user.email_address = args.email

success = create_user(conn, user)
if not success:
    logging.warning("Cannot create user")
