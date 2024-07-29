#! /usr/bin/env python

from argparse import ArgumentParser
from config import read_config
from parser import parse_feed
from subscribe import Category
from subscribe import Subscription
import store
import subscribe

arg_parser = ArgumentParser()
arg_parser.add_argument("-f", "--file", help="file to parse", required=True)

args = arg_parser.parse_args()
config = read_config("config.yaml")

conn = store.Connection()
conn.connect(config.database)

def handle_cat(cat):
    for item in cat.items:
        if type(item) is Category:
            handle_cat(item)
        elif type(item) is Subscription:
            handle_sub(item)

def handle_sub(sub: Subscription):
    try:
        result = parse_feed(sub.url)
        store.store_doc(conn, result)
        print(f"OK! {sub.url}")
    except ValueError as e:
        print(f"--- {sub.url} - {e}")

def main():
    cat = subscribe.parse_google_reader(args.file)
    handle_cat(cat)

main()
