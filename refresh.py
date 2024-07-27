#! /usr/bin/env python

from argparse import ArgumentParser
from parser import parse_feed
from time import gmtime
from time import localtime
from time import mktime
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

conn = store.Connection('reader')
conn.connect("admin", "password", "localhost", 5984)

def main():
    fresh_seconds = args.fresh * 60
    now = mktime(localtime())
    stale_start = gmtime(now - fresh_seconds)

    for feed in store.stale_feeds(conn, stale_start=stale_start):
        # FIXME!! Chunk writes
        feed_url = feed["url"]
        try:
            result = parse_feed(feed_url)
            store.store_doc(conn, result)
            print(f"OK! {feed_url}")
        except ValueError as e:
            print(f"--- {feed_url} - {e}")

main()
