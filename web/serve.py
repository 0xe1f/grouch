#! /usr/bin/env python

# Copyright (C) 2024 Akop Karapetyan
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

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
from flask import send_file
from flask_executor import Executor
from io import BytesIO
from json import loads
import port.objects
from store import BulkUpdateQueue
from store import Connection
from store import fetch_user
from store import find_articles_by_folder
from store import find_articles_by_id
from store import find_articles_by_prop
from store import find_articles_by_tag
from store import find_articles_by_sub
from store import find_articles_by_user
from store import find_entries_by_id
from store import find_feeds_by_id
from store import find_folders_by_id
from store import find_folders_by_user
from store import find_tags_by_user
from store import find_subs_by_id
from store import find_user_id
from store import find_subs_by_user
from web.ext_type import Article as PubArticle
from web.ext_type import Error
from web.ext_type import Folder as PubFolder
from web.ext_type import Subscription as PubSub
from web.ext_type import TableOfContents
from web.ext_type import Tag as PubTag
from web.ext_type import requests
from web.ext_type import responses
import logging
import parser
import port
import tasks

app = Flask(__name__)
executor = Executor(app)

@app.route('/')
def index():
    return render_template(
        "index.html",
        user=user,
    )

@app.route('/subscriptions')
def subscriptions():
    return _fetch_table_of_contents().as_dict()

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
            app.logger.error("Filter is not valid JSON")

    if "f" in filter:
        unread_only = "p" in filter and Article.PROP_UNREAD in filter["p"]
        articles, next_start = find_articles_by_folder(conn, filter["f"], start, unread_only=unread_only)
    elif "s" in filter:
        unread_only = "p" in filter and Article.PROP_UNREAD in filter["p"]
        articles, next_start = find_articles_by_sub(conn, filter["s"], start, unread_only=unread_only)
    elif "p" in filter:
        articles, next_start = find_articles_by_prop(conn, user.id, filter["p"], start)
    elif "t" in filter:
        articles, next_start = find_articles_by_tag(conn, user.id, filter["t"], start)
    else:
        articles, next_start = find_articles_by_user(conn, user.id, start)

    entries = find_entries_by_id(conn, *[article.entry_id for article in articles])
    entry_map = { entry.id:entry for entry in entries }

    return responses.ArticlesResponse(
        articles=[PubArticle(article=article, entry=entry_map[article.entry_id]) for article in articles],
        next_start=obfuscate_json(next_start) if next_start else None,
    ).as_dict()

@app.route('/exportOpml')
def export_opml():
    subs = find_subs_by_user(conn, user.id)
    feeds = find_feeds_by_id(conn, *[sub.feed_id for sub in subs])
    feed_map = { feed.id:feed for feed in feeds }

    output = port.export_opml(
        title=f"{user.username} subscriptions in grouch",
        subs=[(sub, feed_map[sub.feed_id]) for sub in subs],
        folders=find_folders_by_user(conn, user.id),
    )

    return send_file(
        BytesIO(output.encode()),
        as_attachment=True,
        download_name="subscriptions.xml",
        mimetype="application/xml",
    )

@app.route('/subscribe', methods=['POST'])
def subscribe():
    arg = requests.SubscribeRequest(request.json)
    if not arg:
        app.logger.error(f"Empty request")
        return Error("FIXME!!").as_dict()
    elif not arg.url:
        app.logger.error(f"Missing URL")
        return Error("FIXME!!").as_dict()

    # FIXME: validate url

    # Kick off a task
    executor.submit(tasks.subscribe_user_unknown_url, conn, user_id, arg.url)

    return responses.SubscribeResponse().as_dict()

@app.route('/setProperty', methods=['POST'])
def set_property():
    arg = requests.SetPropertyRequest(request.json)
    if not arg:
        app.logger.error(f"Invalid setProperty request {request.json}")
        return Error("FIXME!!").as_dict()
    elif not arg.article_id:
        app.logger.error(f"Missing article id for {request.json}")
        return Error("FIXME!!").as_dict()

    owner_id = Article.extract_owner_id(arg.article_id)
    if owner_id != user.id:
        app.logger.error(f"Unauthorized article ({owner_id}!={user.id})")
        return Error("FIXME!!").as_dict()

    article = first_or_none(find_articles_by_id(conn, arg.article_id))
    if not article:
        return Error("FIXME!!").as_dict()

    if arg.is_set != (arg.prop_name in article.props):
        with BulkUpdateQueue(conn) as bulk_q:
            if arg.prop_name == Article.PROP_UNREAD:
                # Need to also update sub
                sub = first_or_none(find_subs_by_id(conn, article.subscription_id))
                if not sub:
                    return Error("FIXME!!").as_dict()
                sub.unread_count += 1 if arg.is_set else -1
                bulk_q.enqueue_flex(sub)
            article.toggle_prop(arg.prop_name, arg.is_set)
            bulk_q.enqueue_flex(article)

    return article.props

@app.route('/rename', methods=['POST'])
def rename():
    arg = requests.RenameRequest(request.json)
    if not arg:
        app.logger.error(f"Invalid setProperty request {request.json}")
        return Error("FIXME!!").as_dict()
    elif not arg.id:
        app.logger.error(f"Missing object id for {request.json}")
        return Error("FIXME!!").as_dict()
    # FIXME!! validate title

    doc_type = FlexObject.extract_doc_type(arg.id)
    with BulkUpdateQueue(conn) as bulk_q:
        if doc_type == Subscription.DOC_TYPE:
            owner_id = Subscription.extract_owner_id(arg.id)
            if owner_id != user.id:
                app.logger.error(f"Unauthorized sub ({owner_id}!={user.id})")
                return Error("FIXME!!").as_dict()
            obj = first_or_none(find_subs_by_id(conn, arg.id))
            if not obj:
                return Error("FIXME!!").as_dict()
            obj.title = arg.title
            bulk_q.enqueue_flex(obj)
        elif doc_type == Folder.DOC_TYPE:
            owner_id = Folder.extract_owner_id(arg.id)
            if owner_id != user.id:
                app.logger.error(f"Unauthorized folder ({owner_id}!={user.id})")
                return Error("FIXME!!").as_dict()
            obj = first_or_none(find_folders_by_id(conn, arg.id))
            if not obj:
                return Error("FIXME!!").as_dict()
            obj.title = arg.title
            bulk_q.enqueue_flex(obj)
        else:
            app.logger.error(f"Unrecognized doc_type: {doc_type}")
            return Error("FIXME!!").as_dict()

    return responses.RenameResponse(
        toc=_fetch_table_of_contents(),
    ).as_dict()

@app.route('/setTags', methods=['POST'])
def set_tags():
    arg = requests.SetTagsRequest(request.json)
    if not arg:
        app.logger.error(f"Invalid setTags request {request.json}")
        return Error("FIXME!!").as_dict()
    elif not arg.article_id:
        app.logger.error(f"Missing article id for {request.json}")
        return Error("FIXME!!").as_dict()

    new_tags = []
    if arg.tags:
        # Extract unique tags, after trimming each for spaces
        new_tags = list(set([tag.strip() for tag in arg.tags]))
        if len(new_tags) > 5:
            app.logger.error(f"Too many tags ({len(new_tags)})")
            return Error("FIXME!!").as_dict()

    owner_id = Article.extract_owner_id(arg.article_id)
    if owner_id != user.id:
        app.logger.error(f"Unauthorized article ({owner_id}!={user.id})")
        return Error("FIXME!!").as_dict()

    article = first_or_none(find_articles_by_id(conn, arg.article_id))
    if not article:
        return Error("FIXME!!").as_dict()

    with BulkUpdateQueue(conn) as bulk_q:
        article.tags = new_tags
        bulk_q.enqueue_flex(article)

    return responses.SetTagsResponse(
        toc=_fetch_table_of_contents(),
        tags=article.tags,
    ).as_dict()

@app.route('/createFolder', methods=['POST'])
def create_folder():
    arg = requests.CreateFolderRequest(request.json)
    if not arg:
        app.logger.error(f"Invalid createFolder request {request.json}")
        return Error("FIXME!!").as_dict()
    elif not arg.title:
        app.logger.error(f"Missing title for {request.json}")
        return Error("FIXME!!").as_dict()

    with BulkUpdateQueue(conn) as bulk_q:
        folder = Folder()
        folder.title = arg.title
        folder.user_id = user.id
        bulk_q.enqueue_flex(folder)

    return responses.CreateFolderResponse(
        toc=_fetch_table_of_contents(),
    ).as_dict()

@app.route('/moveSub', methods=['POST'])
def move_sub():
    arg = requests.MoveSubRequest(request.json)
    if not arg:
        app.logger.error(f"Empty request")
        return Error("FIXME!!").as_dict()
    elif not arg.id:
        app.logger.error(f"Missing id")
        return Error("FIXME!!").as_dict()

    source_owner_id = Subscription.extract_owner_id(arg.id)
    if source_owner_id != user.id:
        app.logger.error(f"Unauthorized source ({source_owner_id}!={user.id})")
        return Error("FIXME!!").as_dict()

    if arg.destination:
        dest_owner_id = Folder.extract_owner_id(arg.destination)
        if dest_owner_id != user.id:
            app.logger.error(f"Unauthorized destination ({dest_owner_id}!={user.id})")
            return Error("FIXME!!").as_dict()
        folder = first_or_none(find_folders_by_id(conn, arg.destination))
        if not folder:
            app.logger.error(f"Destination ({arg.destination}) does not exist")
            return Error("FIXME!!").as_dict()

    # Move the subscription
    with BulkUpdateQueue(conn) as bulk_q:
        sub = first_or_none(find_subs_by_id(conn, arg.id))
        if not sub:
            app.logger.error(f"Sub ({arg.id}) does not exist")
            return Error("FIXME!!").as_dict()
        sub.folder_id = arg.destination
        bulk_q.enqueue_flex(sub)

    # Move the articles asynchronously
    if bulk_q.written_count > 0:
        executor.submit(tasks.move_articles, conn, arg.id, arg.destination)

    return responses.MoveSubResponse(
        toc=_fetch_table_of_contents(),
    ).as_dict()

@app.route('/removeTag', methods=['POST'])
def remove_tag():
    arg = requests.RemoveTagRequest(request.json)
    if not arg:
        app.logger.error(f"Empty request")
        return Error("FIXME!!").as_dict()
    elif not arg.tag:
        app.logger.error(f"Missing tag")
        return Error("FIXME!!").as_dict()

    # Remove tags asynchronously
    executor.submit(tasks.remove_tag_from_articles, conn, user.id, arg.tag)

    # Remove it from the list manually
    toc = _fetch_table_of_contents()
    toc.remove_tag(arg.tag)

    return responses.MoveSubResponse(toc).as_dict()

@app.route('/unsubscribe', methods=['POST'])
def unsubscribe():
    arg = requests.UnsubscribeRequest(request.json)
    if not arg:
        app.logger.error(f"Empty request")
        return Error("FIXME!!").as_dict()

    if not arg.id:
        app.logger.error(f"Missing id")
        return Error("FIXME!!").as_dict()

    owner_id = Subscription.extract_owner_id(arg.id)
    if owner_id != user.id:
        app.logger.error(f"Unauthorized object ({owner_id}!={user.id})")
        return Error("FIXME!!").as_dict()

    executor.submit(tasks.unsubscribe, conn, arg.id)
    toc = _fetch_table_of_contents()
    # Actual deletion will happen asynchronously
    toc.remove_subscription(arg.id)

    return responses.UnsubscribeResponse(toc).as_dict()

@app.route('/deleteFolder', methods=['POST'])
def delete_folder():
    arg = requests.DeleteFolderRequest(request.json)
    if not arg:
        app.logger.error(f"Empty request")
        return Error("FIXME!!").as_dict()

    if not arg.id:
        app.logger.error(f"Missing id")
        return Error("FIXME!!").as_dict()

    owner_id = Folder.extract_owner_id(arg.id)
    if owner_id != user.id:
        app.logger.error(f"Unauthorized object ({owner_id}!={user.id})")
        return Error("FIXME!!").as_dict()

    executor.submit(tasks.delete_folder, conn, arg.id)
    toc = _fetch_table_of_contents()
    # Actual deletion will happen asynchronously
    toc.remove_folder(arg.id)

    return responses.DeleteFolderResponse(toc).as_dict()

@app.route('/markAllAsRead', methods=['POST'])
def mark_all_as_read():
    arg = requests.MarkAllAsReadRequest(request.json)
    if not arg:
        app.logger.error(f"Empty request")
        return Error("FIXME!!").as_dict()

    match arg.scope:
        case requests.MarkAllAsReadRequest.SCOPE_ALL:
            executor.submit(tasks.mark_subs_read_by_user, conn, user.id)
        case requests.MarkAllAsReadRequest.SCOPE_FOLDER:
            if not arg.id:
                app.logger.error(f"Missing id")
                return Error("FIXME!!").as_dict()
            owner_id = Folder.extract_owner_id(arg.id)
            if owner_id != user.id:
                app.logger.error(f"Unauthorized object ({owner_id}!={user.id})")
                return Error("FIXME!!").as_dict()

            executor.submit(tasks.mark_subs_read_by_folder, conn, arg.id)
        case requests.MarkAllAsReadRequest.SCOPE_SUB:
            if not arg.id:
                app.logger.error(f"Missing id")
                return Error("FIXME!!").as_dict()

            owner_id = Subscription.extract_owner_id(arg.id)
            if owner_id != user.id:
                app.logger.error(f"Unauthorized object ({owner_id}!={user.id})")
                return Error("FIXME!!").as_dict()

            executor.submit(tasks.mark_sub_read, conn, arg.id)

    toc = _fetch_table_of_contents()
    match arg.scope:
        case requests.MarkAllAsReadRequest.SCOPE_ALL:
            toc.mark_all_as_read()
        case requests.MarkAllAsReadRequest.SCOPE_FOLDER:
            toc.mark_folder_as_read(arg.id)
        case requests.MarkAllAsReadRequest.SCOPE_SUB:
            toc.mark_sub_as_read(arg.id)

    return responses.MarkAllAsReadResponse(toc).as_dict()

def _fetch_table_of_contents() -> TableOfContents:
    subs = find_subs_by_user(conn, user.id)
    feeds = find_feeds_by_id(conn, *[sub.feed_id for sub in subs])
    folders = find_folders_by_user(conn, user.id)
    feed_map = { feed.id:feed for feed in feeds }
    tags = find_tags_by_user(conn, user.id)

    return TableOfContents(
        subs=[PubSub(sub, feed_map[sub.feed_id]) for sub in subs],
        folders=[PubFolder(folder) for folder in folders],
        tags=[PubTag(tag) for tag in tags],
    )

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    config = read_config("config.yaml")

    conn = Connection()
    conn.connect(config.database)

    user_id = find_user_id(conn, "foo")
    user = fetch_user(conn, user_id)

    app.config['EXECUTOR_PROPAGATE_EXCEPTIONS'] = True
    app.run(host='0.0.0.0', port='8080', debug=True)
