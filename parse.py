#! /usr/bin/env python

from argparse import ArgumentParser
from subscribe import Category
from subscribe import Subscription
from parser import parse_feed
import store
import subscribe

arg_parser = ArgumentParser()
arg_parser.add_argument("-f", "--file", help="file to parse", required=True)

args = arg_parser.parse_args()

conn = store.Connection('reader')
conn.connect("admin", "password", "localhost", 5984)

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

cat = subscribe.parse_google_reader(args.file)
handle_cat(cat)
