#! /usr/bin/env python

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
