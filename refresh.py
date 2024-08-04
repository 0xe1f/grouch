#! /usr/bin/env python

from argparse import ArgumentParser
from config import read_config
from tasks import refresh_feeds
import logging
import store

arg_parser = ArgumentParser()
arg_parser.add_argument(
    "-f",
    "--fresh",
    help="freshness duration, in minutes",
    required=True,
    type=int
)

args = arg_parser.parse_args()
config = read_config("config.yaml")
logging.basicConfig(level=logging.DEBUG)

conn = store.Connection()
conn.connect(config.database)

def main():
    freshness_seconds = args.fresh * 60
    refresh_feeds(conn, freshness_seconds)

main()
