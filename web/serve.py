#! /usr/bin/env python

from common.lists import first_or_none
from common.secret import deobfuscate_json
from common.secret import obfuscate_json
from config import read_config
from datatype import Article
from datatype import Folder
from datatype import Subscription
from datatype import FlexObject
from flask import Flask
from flask import render_template
from flask import request
from json import loads
from store import BulkUpdateQueue
from store import Connection
from store import fetch_user
from store import find_articles_by_id
from store import find_articles_by_prop
from store import find_articles_by_sub
from store import find_articles_by_user
from store import find_entries_by_id
from store import find_feeds_by_id
from store import find_folders_by_id
from store import find_subs_by_id
from store import find_user_id
from store import find_user_subs
from web.ext_type import Error
from web.ext_type import Folder as PubFolder
from web.ext_type import SetProperty
from web.ext_type import ArticlePage
from web.ext_type import PublicArticle
from web.ext_type import PublicSub
from web.ext_type import Rename
from web.ext_type import TableOfContents
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

    return TableOfContents(
        subs=[PublicSub(sub, feed_map[sub.feed_id]) for sub in subs],
        folders=[PubFolder()],
    ).as_dict()

@app.route('/articles')
def articles():
    rq_args = request.args

    start = None
    if "continue" in rq_args:
        start = deobfuscate_json(rq_args["continue"])

    filter = {}
    if "filter" in rq_args:
        try:
            filter = loads(rq_args["filter"])
        except ValueError:
            logging.error("Filter is not valid JSON")

    if "s" in filter:
        unread_only = "p" in filter and Article.PROP_UNREAD in filter["p"]
        articles, next_start = find_articles_by_sub(conn, filter["s"], start, unread_only=unread_only)
    elif "p" in filter:
        articles, next_start = find_articles_by_prop(conn, user.id, filter["p"], start)
    else:
        articles, next_start = find_articles_by_user(conn, user.id, start)

    entries = find_entries_by_id(conn, *[article.entry_id for article in articles])
    entry_map = { entry.id:entry for entry in entries }

    return ArticlePage(
        next_start=obfuscate_json(next_start) if next_start else None,
        articles=[PublicArticle(article=article, entry=entry_map[article.entry_id]) for article in articles],
    ).as_dict()

@app.route('/setProperty', methods=['POST'])
def set_property():
    arg = SetProperty(request.json)
    if not arg:
        logging.warning(f"Invalid setProperty request {request.json}")
        return Error("FIXME!!").as_dict()
    elif not arg.article_id:
        logging.warning(f"Missing article id for {request.json}")
        return Error("FIXME!!").as_dict()

    owner_id = Article.extract_owner_id(arg.article_id)
    if owner_id != user.id:
        logging.warning(f"User not authorized ({owner_id}!={user.id})")
        return Error("FIXME!!").as_dict()

    article = first_or_none(find_articles_by_id(conn, arg.article_id))
    if not article:
        return Error("FIXME!!").as_dict()

    if arg.is_set != (arg.prop_name in article.props):
        bulk_q = BulkUpdateQueue(conn)
        if arg.prop_name == Article.PROP_UNREAD:
            # Need to also update sub
            sub = first_or_none(find_subs_by_id(conn, article.subscription_id))
            if not sub:
                return Error("FIXME!!").as_dict()
            sub.unread_count += 1 if arg.is_set else -1
            bulk_q.enqueue_tuple((sub.doc(), sub))
        article.toggle_prop(arg.prop_name, arg.is_set)
        bulk_q.enqueue_tuple((article.doc(), article))
        bulk_q.flush()

    return article.props

@app.route('/rename', methods=['POST'])
def rename():
    arg = Rename(request.json)
    if not arg:
        logging.warning(f"Invalid setProperty request {request.json}")
        return Error("FIXME!!").as_dict()
    elif not arg.id:
        logging.warning(f"Missing object id for {request.json}")
        return Error("FIXME!!").as_dict()
    # FIXME!! validate title

    doc_type = FlexObject.extract_doc_type(arg.id)
    bulk_q = BulkUpdateQueue(conn)
    if doc_type == Subscription.DOC_TYPE:
        owner_id = Subscription.extract_owner_id(arg.id)
        if owner_id != user.id:
            logging.warning(f"User not authorized ({owner_id}!={user.id})")
            return Error("FIXME!!").as_dict()
        obj = first_or_none(find_subs_by_id(conn, arg.id))
        if not obj:
            return Error("FIXME!!").as_dict()
        obj.title = arg.title
        bulk_q.enqueue_tuple((obj.doc(), obj))
    elif doc_type == Folder.DOC_TYPE:
        owner_id = Folder.extract_owner_id(arg.id)
        if owner_id != user.id:
            logging.warning(f"User not authorized ({owner_id}!={user.id})")
            return Error("FIXME!!").as_dict()
        obj = first_or_none(find_folders_by_id(conn, arg.id))
        if not obj:
            return Error("FIXME!!").as_dict()
        obj.title = arg.title
        bulk_q.enqueue_tuple((obj.doc(), obj))
    else:
        logging.warning(f"Unrecognized doc_type: {doc_type}")
        return Error("FIXME!!").as_dict()

    bulk_q.flush()

    # FIXME!!: return the entire tree?

    return {}

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    config = read_config("config.yaml")

    conn = Connection()
    conn.connect(config.database)

    user_id = find_user_id(conn, "foo")
    user = fetch_user(conn, user_id)

    app.run(host='0.0.0.0', port='8080', debug=True)
