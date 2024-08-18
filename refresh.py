#! /usr/bin/env python

from argparse import ArgumentParser
from tasks import refresh_feeds
import logging
import store
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

conn = store.Connection()
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
