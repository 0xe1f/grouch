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

from common.secret import deobfuscate_json
from common.secret import obfuscate_json
from datatype import Article
from datatype import Folder
from datatype import Subscription
from datetime import datetime
from datetime import timedelta
from flask_executor import Executor
from flask_socketio import SocketIO
from io import BytesIO
from store import BulkUpdateQueue
from store import Connection
from store import fetch_user
from store import find_articles_by_folder
from store import find_articles_by_prop
from store import find_articles_by_tag
from store import find_articles_by_sub
from store import find_articles_by_user
from store import find_entries_by_id
from store import find_feeds_by_id
from store import find_folders_by_user
from store import find_tags_by_user
from store import find_user_id
from store import find_subs_by_user
from tasks.objects import TaskContext
from tasks.objects import TaskException
from web.ext_type import requests
from web.ext_type import responses
import flask
import flask_login
import logging
import os.path
import port
import re
import tasks.async_tasks as async_tasks
import tasks.sync_tasks as sync_tasks
import tempfile
import tomllib
import web.ext_type.objects as ext_objs

app = flask.Flask(__name__)
app.config.from_file("../config_defaults.toml", load=tomllib.load, text=False)
app.config.from_file("../config.toml", load=tomllib.load, text=False)
socketio = SocketIO(app)
executor = Executor(app)

login_manager = flask_login.LoginManager()
login_manager.login_view = "/login"
login_manager.init_app(app)

user_sessions = {}

FEED_SYNC_TIMEOUT = 600 # 10 min
UPLOAD_ALLOWED_TYPES = [ ".xml" ]
REGEX_REDIRECT_URL = re.compile(r"^(/\w+)+|/$")

@login_manager.user_loader
def load_user(user_id):
    return ext_objs.User(user=fetch_user(conn, user_id))

@app.get("/login")
def login_get():
    return flask.render_template(
        "login.html",
    )

@app.post("/login")
def login_post():
    arg = requests.LoginRequest(flask.request.form)

    try:
        arg.validate()
    except requests.ValidationException as e:
        app.logger.error(e.message)
        return ext_objs.Error("FIXME!!").as_dict()

    try:
        user = sync_tasks.users_authenticate(
            _create_task_context(),
            arg.username,
            arg.password
        )
    except TaskException as e:
        app.logger.error(e.message)
        return ext_objs.Error("FIXME!!").as_dict()

    flask_login.utils.login_user(ext_objs.User(user))

    if next := flask.request.args.get("next"):
        if not REGEX_REDIRECT_URL.fullmatch(next):
            logging.warn(f"{next} is not a valid redirection URL")
            next = None

    return flask.redirect(next or flask.url_for("/"))

@app.route("/")
@flask_login.login_required
def index():
    return flask.render_template(
        "index.html",
        user=user,
    )

@app.route("/subscriptions")
@flask_login.login_required
def subscriptions():
    return _fetch_table_of_contents().as_dict()

@app.route("/articles")
@flask_login.login_required
def articles():
    arg = requests.ArticlesRequest(flask.request.args)

    start = None
    if arg.start:
        start = deobfuscate_json(arg.start)

    if arg.folder:
        unread_only = arg.prop == Article.PROP_UNREAD
        articles, next_start = find_articles_by_folder(conn, arg.folder, start, unread_only=unread_only)
    elif arg.sub:
        unread_only = arg.prop == Article.PROP_UNREAD
        articles, next_start = find_articles_by_sub(conn, arg.sub, start, unread_only=unread_only)
    elif arg.prop:
        articles, next_start = find_articles_by_prop(conn, user.id, arg.prop, start)
    elif arg.tag:
        articles, next_start = find_articles_by_tag(conn, user.id, arg.tag, start)
    else:
        articles, next_start = find_articles_by_user(conn, user.id, start)

    entries = find_entries_by_id(conn, *[article.entry_id for article in articles])
    entry_map = { entry.id:entry for entry in entries }

    return responses.ArticlesResponse(
        articles=[ext_objs.Article(article=article, entry=entry_map[article.entry_id]) for article in articles],
        next_start=obfuscate_json(next_start) if next_start else None,
    ).as_dict()

@app.route("/exportOpml")
@flask_login.login_required
def export_opml():
    subs = find_subs_by_user(conn, user.id)
    feeds = find_feeds_by_id(conn, *[sub.feed_id for sub in subs])
    feed_map = { feed.id:feed for feed in feeds }

    output = port.export_opml(
        title=f"{user.username} subscriptions in grouch",
        subs=[(sub, feed_map[sub.feed_id]) for sub in subs],
        folders=find_folders_by_user(conn, user.id),
    )

    return flask.send_file(
        BytesIO(output.encode()),
        as_attachment=True,
        download_name="subscriptions.xml",
        mimetype="application/xml",
    )

@app.route("/subscribe", methods=["POST"])
@flask_login.login_required
def subscribe():
    if not (arg := requests.SubscribeRequest(flask.request.json)):
        app.logger.error(f"Empty request")
        return ext_objs.Error("FIXME!!").as_dict()
    elif not arg.url:
        app.logger.error(f"Missing URL")
        return ext_objs.Error("FIXME!!").as_dict()

    # FIXME: validate url

    # Kick off a task
    executor.submit(async_tasks.subs_subscribe_url, _create_task_context(), arg.url)

    return responses.SubscribeResponse().as_dict()

@app.route("/setProperty", methods=["POST"])
@flask_login.login_required
def set_property():
    if not (arg := requests.SetPropertyRequest(flask.request.json)):
        app.logger.error(f"Empty request")
        return ext_objs.Error("FIXME!!").as_dict()

    try:
        article = sync_tasks.articles_set_property(
            _create_task_context(),
            arg.article_id,
            arg.prop_name,
            arg.is_set,
        )
    except TaskException as e:
        app.logger.error(e.message)
        return ext_objs.Error("FIXME!!").as_dict()

    return article.props

@app.route("/rename", methods=["POST"])
@flask_login.login_required
def rename():
    if not (arg := requests.RenameRequest(flask.request.json)):
        app.logger.error(f"Empty request")
        return ext_objs.Error("FIXME!!").as_dict()

    try:
        sync_tasks.objects_rename(
            _create_task_context(),
            arg.article_id,
            arg.prop_name,
            arg.is_set,
        )
    except TaskException as e:
        app.logger.error(e.message)
        return ext_objs.Error("FIXME!!").as_dict()

    return responses.RenameResponse(
        toc=_fetch_table_of_contents(),
    ).as_dict()

@app.route("/setTags", methods=["POST"])
@flask_login.login_required
def set_tags():
    if not (arg := requests.SetTagsRequest(flask.request.json)):
        app.logger.error(f"Empty request")
        return ext_objs.Error("FIXME!!").as_dict()

    try:
        article = sync_tasks.articles_set_tags(
            _create_task_context(),
            arg.article_id,
            arg.tags,
        )
    except TaskException as e:
        app.logger.error(e.message)
        return ext_objs.Error("FIXME!!").as_dict()

    return responses.SetTagsResponse(
        toc=_fetch_table_of_contents(),
        tags=article.tags,
    ).as_dict()

@app.route("/createFolder", methods=["POST"])
@flask_login.login_required
def create_folder():
    if not (arg := requests.CreateFolderRequest(flask.request.json)):
        app.logger.error(f"Empty request")
        return ext_objs.Error("FIXME!!").as_dict()

    try:
        sync_tasks.folders_create(
            _create_task_context(),
            arg.title,
        )
    except TaskException as e:
        app.logger.error(e.message)
        return ext_objs.Error("FIXME!!").as_dict()

    return responses.CreateFolderResponse(
        toc=_fetch_table_of_contents(),
    ).as_dict()

@app.route("/moveSub", methods=["POST"])
@flask_login.login_required
def move_sub():
    if not (arg := requests.MoveSubRequest(flask.request.json)):
        app.logger.error(f"Empty request")
        return ext_objs.Error("FIXME!!").as_dict()

    sync_tasks.subs_move(
        _create_task_context(),
        arg.id,
        arg.destination,
    )

    return responses.MoveSubResponse(
        toc=_fetch_table_of_contents(),
    ).as_dict()

@app.route("/removeTag", methods=["POST"])
@flask_login.login_required
def remove_tag():
    arg = requests.RemoveTagRequest(flask.request.json)
    if not arg:
        app.logger.error(f"Empty request")
        return ext_objs.Error("FIXME!!").as_dict()
    elif not arg.tag:
        app.logger.error(f"Missing tag")
        return ext_objs.Error("FIXME!!").as_dict()

    # Remove tags asynchronously
    executor.submit(async_tasks.articles_remove_tag, _create_task_context(), arg.tag)

    # Remove it from the list manually
    toc = _fetch_table_of_contents()
    toc.remove_tag(arg.tag)

    return responses.MoveSubResponse(toc).as_dict()

@app.route("/unsubscribe", methods=["POST"])
@flask_login.login_required
def unsubscribe():
    if not (arg := requests.UnsubscribeRequest(flask.request.json)):
        app.logger.error(f"Empty request")
        return ext_objs.Error("FIXME!!").as_dict()

    sync_tasks.subs_unsubscribe(
        _create_task_context(),
        arg.id,
    )

    # Actual deletion will happen asynchronously
    toc = _fetch_table_of_contents()
    toc.remove_subscription(arg.id)

    return responses.UnsubscribeResponse(toc).as_dict()

@app.route("/deleteFolder", methods=["POST"])
@flask_login.login_required
def delete_folder():
    if not (arg := requests.DeleteFolderRequest(flask.request.json)):
        app.logger.error(f"Empty request")
        return ext_objs.Error("FIXME!!").as_dict()

    sync_tasks.folders_delete(
        _create_task_context(),
        arg.id,
    )

    # Actual deletion will happen asynchronously
    toc = _fetch_table_of_contents()
    toc.remove_folder(arg.id)

    return responses.DeleteFolderResponse(toc).as_dict()

@app.route("/markAllAsRead", methods=["POST"])
@flask_login.login_required
def mark_all_as_read():
    if not (arg := requests.MarkAllAsReadRequest(flask.request.json)):
        app.logger.error(f"Empty request")
        return ext_objs.Error("FIXME!!").as_dict()

    match arg.scope:
        case requests.MarkAllAsReadRequest.SCOPE_ALL:
            executor.submit(async_tasks.subs_mark_read_by_user, _create_task_context())
        case requests.MarkAllAsReadRequest.SCOPE_FOLDER:
            if not arg.id:
                app.logger.error(f"Missing id")
                return ext_objs.Error("FIXME!!").as_dict()
            elif (owner_id := Folder.extract_owner_id(arg.id)) != user.id:
                app.logger.error(f"Unauthorized object ({owner_id}!={user.id})")
                return ext_objs.Error("FIXME!!").as_dict()

            executor.submit(async_tasks.subs_mark_read_by_folder, _create_task_context(), arg.id)
        case requests.MarkAllAsReadRequest.SCOPE_SUB:
            if not arg.id:
                app.logger.error(f"Missing id")
                return ext_objs.Error("FIXME!!").as_dict()
            elif (owner_id := Subscription.extract_owner_id(arg.id)) != user.id:
                app.logger.error(f"Unauthorized object ({owner_id}!={user.id})")
                return ext_objs.Error("FIXME!!").as_dict()

            executor.submit(async_tasks.subs_mark_read_by_sub, _create_task_context(), arg.id)

    toc = _fetch_table_of_contents()
    match arg.scope:
        case requests.MarkAllAsReadRequest.SCOPE_ALL:
            toc.mark_all_as_read()
        case requests.MarkAllAsReadRequest.SCOPE_FOLDER:
            toc.mark_folder_as_read(arg.id)
        case requests.MarkAllAsReadRequest.SCOPE_SUB:
            toc.mark_sub_as_read(arg.id)

    return responses.MarkAllAsReadResponse(toc).as_dict()

@app.route("/syncFeeds", methods=["POST"])
@flask_login.login_required
def sync_feeds():
    now = datetime.now()
    if last_sync := user.last_sync:
        last_sync_dt = datetime.fromtimestamp(last_sync)
        delta = now - last_sync_dt
        if delta.total_seconds() < FEED_SYNC_TIMEOUT:
            return responses.SyncFeedsResponse(
                next_sync=(now + delta).timestamp(),
            ).as_dict()
        else:
           last_sync = None

    if not last_sync:
        user.last_sync = now.timestamp()
        with BulkUpdateQueue(conn) as bulk_q:
            bulk_q.enqueue_flex(user)

    executor.submit(async_tasks.subs_sync, _create_task_context())

    return responses.SyncFeedsResponse(
        toc=_fetch_table_of_contents(),
        next_sync=(now + timedelta(seconds=FEED_SYNC_TIMEOUT)).timestamp(),
    ).as_dict()

@app.route("/importFeeds", methods=["POST"])
@flask_login.login_required
def import_feeds():
    # Check individual files
    if "file" not in flask.request.files:
        app.logger.error(f"No file in request")
        return ext_objs.Error("FIXME!!").as_dict()

    if not (file := flask.request.files["file"]) or file.filename == "":
        app.logger.error(f"No filename in file")
        return ext_objs.Error("FIXME!!").as_dict()

    _, ext = os.path.splitext(file.filename)
    if ext not in UPLOAD_ALLOWED_TYPES:
        app.logger.error(f"Unsupported file type: '{ext}'")
        return ext_objs.Error("FIXME!!").as_dict()

    with tempfile.TemporaryFile() as tmp:
        file.save(tmp)
        tmp.seek(0)

        doc = port.import_opml(tmp)

    if not doc:
        app.logger.error(f"Unable to import document")
        return ext_objs.Error("FIXME!!").as_dict()

    executor.submit(async_tasks.subs_import, _create_task_context(), doc)

    return responses.ImportFeedsResponse().as_dict()

@socketio.on("connect")
def test_connect(auth):
    sessions = user_sessions.setdefault(user.id, [])
    sessions.append(flask.request.sid)

    socketio.emit("fef", { "wowie": "zowie" }, to=flask.request.sid)
    logging.info(f"connect: {user_sessions}")

@socketio.on("disconnect")
def disconnect():
    logging.info(f"{user_sessions}")

    # Not atomic
    if flask.request.sid in (sessions := user_sessions.setdefault(user.id, [])):
        sessions.remove(flask.request.sid)

    logging.info(f"connect: {user_sessions}")

def _create_task_context() -> TaskContext:
    return TaskContext(
        conn,
        user.id,
        None,
        executor.submit,
    )

def _fetch_table_of_contents() -> ext_objs.TableOfContents:
    subs = find_subs_by_user(conn, user.id)
    feeds = find_feeds_by_id(conn, *[sub.feed_id for sub in subs])
    folders = find_folders_by_user(conn, user.id)
    feed_map = { feed.id:feed for feed in feeds }
    tags = find_tags_by_user(conn, user.id)

    return ext_objs.TableOfContents(
        subs=[ext_objs.Subscription(sub, feed_map[sub.feed_id]) for sub in subs],
        folders=[ext_objs.Folder(folder) for folder in folders],
        tags=[ext_objs.Tag(tag) for tag in tags],
    )

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)

    conn = Connection()
    conn.connect(
        app.config["DATABASE_NAME"],
        app.config["DATABASE_USERNAME"],
        app.config["DATABASE_PASSWORD"],
        app.config["DATABASE_HOST"],
        app.config.get("DATABASE_PORT")
    )

    user_id = find_user_id(conn, "foo")
    user = fetch_user(conn, user_id)

    # app.run(host='0.0.0.0', port='8080', debug=True)
    socketio.run(app, host='0.0.0.0', port='8080', debug=True)
