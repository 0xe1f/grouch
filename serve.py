#! /usr/bin/env python

from config import read_config
from datatype import Filter
from datatype import PublicArticle
from datatype import PublicSub
from flask import Flask
from flask import render_template
from flask import request
from json import loads
from store import Connection
from store import fetch_user
from store import find_articles_by_sub
from store import find_articles_by_user
from store import find_entries_by_id
from store import find_feeds_by_id
from store import find_user_id
from store import find_user_subs
import logging

app = Flask(__name__)

@app.route('/')
def index():
    return render_template(
        "index.html",
        user=user,
    )

@app.route('/subscriptions')
def subscriptions():
    subs = find_user_subs(conn, user.id)
    feeds = find_feeds_by_id(conn, *[sub.feed_id for sub in subs])
    feed_map = { feed.id:feed for feed in feeds }

    # FIXME
    return {
        "folders": [],
        "tags": [],
        "subscriptions": [PublicSub(sub, feed_map[sub.feed_id]).doc() for sub in subs],
    }

@app.route('/articles')
def articles():
    filter = _parse_filter(request.args.get("filter"))
    if filter.subscription_id:
        articles = find_articles_by_sub(conn, filter.subscription_id)
    else:
        articles = find_articles_by_user(conn, user.id)

    entries = find_entries_by_id(conn, *[article.entry_id for article in articles])
    entry_map = { entry.id:entry for entry in entries }

    return {
        "articles": [PublicArticle(article, entry_map[article.entry_id]).doc() for article in articles]
    }

def _parse_filter(doc: str):
    json = loads(doc)
    if "s" in json:
        return Filter(sub_id=json["s"])

    return Filter()

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    config = read_config("config.yaml")

    conn = Connection()
    conn.connect(config.database)

    user_id = find_user_id(conn, "foo")
    user = fetch_user(conn, user_id)

    app.run(host='0.0.0.0', port='8080', debug=True)
