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
from flask_executor import Executor
from flask_login import current_user
from io import BytesIO
from dao import Connection
from dao import Database
from tasks.objects import TaskContext
from tasks.objects import TaskException
from web.ext_type import requests
from web.ext_type import responses
import flask
import flask_login
import flask_socketio
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
socketio = flask_socketio.SocketIO(app)
executor = Executor(app)

login_manager = flask_login.LoginManager()
login_manager.login_view = "/login"
login_manager.init_app(app)

FEED_SYNC_TIMEOUT_SECS = 600 # 10 min
UPLOAD_ALLOWED_TYPES = [ ".xml" ]
REGEX_REDIRECT_URL = re.compile(r"^(/\w+)+|/$")

@login_manager.user_loader
def load_user(user_id):
    return ext_objs.User(user=stores.users.find_by_id(user_id))

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

@app.get("/")
@flask_login.login_required
def index():
    return flask.render_template(
        "index.html",
    )

@app.get("/subscriptions")
@flask_login.login_required
def subscriptions():
    return _fetch_table_of_contents().as_dict()

@app.get("/articles")
@flask_login.login_required
def articles():
    arg = requests.ArticlesRequest(flask.request.args)

    start = None
    if arg.start:
        start = deobfuscate_json(arg.start)

    if arg.folder:
        unread_only = arg.prop == Article.PROP_UNREAD
        articles, next_start = stores.articles.get_page_by_folder(arg.folder, start, unread_only=unread_only)
    elif arg.sub:
        unread_only = arg.prop == Article.PROP_UNREAD
        articles, next_start = stores.articles.get_page_by_sub(arg.sub, start, unread_only=unread_only)
    elif arg.prop:
        articles, next_start = stores.articles.get_page_by_prop(current_user.id, arg.prop, start)
    elif arg.tag:
        articles, next_start = stores.articles.get_page_by_tag(current_user.id, arg.tag, start)
    else:
        articles, next_start = stores.articles.get_page_by_user(current_user.id, start)

    entries = stores.entries.find_by_id(*[article.entry_id for article in articles])
    entry_map = { entry.id:entry for entry in entries }

    return responses.ArticlesResponse(
        articles=[ext_objs.Article(article=article, entry=entry_map[article.entry_id]) for article in articles],
        next_start=obfuscate_json(next_start) if next_start else None,
    ).as_dict()

@app.get("/exportOpml")
@flask_login.login_required
def export_opml():
    subs = stores.subs.find_by_user(current_user.id)
    feeds = stores.feeds.find_by_id(*[sub.feed_id for sub in subs])
    feed_map = { feed.id:feed for feed in feeds }

    output = port.export_opml(
        title=f"{current_user.username} subscriptions in grouch",
        subs=[(sub, feed_map[sub.feed_id]) for sub in subs],
        folders=stores.folders.find_by_user(current_user.id),
    )

    return flask.send_file(
        BytesIO(output.encode()),
        as_attachment=True,
        download_name="subscriptions.xml",
        mimetype="application/xml",
    )

@app.post("/subscribe")
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

@app.post("/setProperty")
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

@app.post("/rename")
@flask_login.login_required
def rename():
    if not (arg := requests.RenameRequest(flask.request.json)):
        app.logger.error(f"Empty request")
        return ext_objs.Error("FIXME!!").as_dict()

    try:
        sync_tasks.objects_rename(
            _create_task_context(),
            arg.id,
            arg.title,
        )
    except TaskException as e:
        app.logger.error(e.message)
        return ext_objs.Error("FIXME!!").as_dict()

    return responses.RenameResponse(
        toc=_fetch_table_of_contents(),
    ).as_dict()

@app.post("/setTags")
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

@app.post("/createFolder")
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

@app.post("/moveSub")
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

@app.post("/removeTag")
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

@app.post("/unsubscribe")
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

@app.post("/deleteFolder")
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

@app.post("/markAllAsRead")
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
            elif (owner_id := Folder.extract_owner_id(arg.id)) != current_user.id:
                app.logger.error(f"Unauthorized object ({owner_id}!={current_user.id})")
                return ext_objs.Error("FIXME!!").as_dict()

            executor.submit(async_tasks.subs_mark_read_by_folder, _create_task_context(), arg.id)
        case requests.MarkAllAsReadRequest.SCOPE_SUB:
            if not arg.id:
                app.logger.error(f"Missing id")
                return ext_objs.Error("FIXME!!").as_dict()
            elif (owner_id := Subscription.extract_owner_id(arg.id)) != current_user.id:
                app.logger.error(f"Unauthorized object ({owner_id}!={current_user.id})")
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

@app.post("/syncFeeds")
@flask_login.login_required
def sync_feeds():
    try:
        next_sync = sync_tasks.subs_sync(
            _create_task_context(),
            datetime.now(),
            FEED_SYNC_TIMEOUT_SECS,
        )
    except TaskException as e:
        app.logger.error(e.message)
        return ext_objs.Error("FIXME!!").as_dict()

    return responses.SyncFeedsResponse(
        next_sync=next_sync.isoformat(),
    ).as_dict()

@app.post("/importFeeds")
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
def socketio_connect():
    if not current_user.is_authenticated:
        logging.warning("Unauthenticated user; disconnecting")
        socketio.disconnect()
        return False

    flask_socketio.join_room(current_user.id)
    app.logger.debug(f"Connected; joined {current_user.id}")

@socketio.on("disconnect")
def socketio_disconnect():
    flask_socketio.leave_room(current_user.id)
    app.logger.debug("Disconnected")

def _create_task_context() -> TaskContext:
    return TaskContext(
        stores,
        current_user.id,
        executor.submit,
        _send_message,
    )

def _fetch_table_of_contents() -> ext_objs.TableOfContents:
    subs = stores.subs.find_by_user(current_user.id)
    feeds = stores.feeds.find_by_id(*[sub.feed_id for sub in subs])
    folders = stores.folders.find_by_user(current_user.id)
    feed_map = { feed.id:feed for feed in feeds }
    tags = stores.articles.find_tags_by_user(current_user.id)

    return ext_objs.TableOfContents(
        subs=[ext_objs.Subscription(sub, feed_map[sub.feed_id]) for sub in subs],
        folders=[ext_objs.Folder(folder) for folder in folders],
        tags=[ext_objs.Tag(tag) for tag in tags],
    )

def _send_message(message_name: str, payload):
    if current_user.is_authenticated:
        socketio.emit(message_name, payload, to=current_user.id)
    else:
        app.logger.warning(f"Cannot send {message_name}; user not authenticated")

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)

    conn = Connection()
    conn.connect(
        app.config["DATABASE_NAME"],
        app.config["DATABASE_USERNAME"],
        app.config["DATABASE_PASSWORD"],
        app.config["DATABASE_HOST"],
        app.config["DATABASE_PORT"],
    )
    stores = Database(conn.db)

    # app.run(host='0.0.0.0', port='8080', debug=True)
    socketio.run(app, host='0.0.0.0', port='8080', debug=True)
