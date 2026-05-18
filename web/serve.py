#! /usr/bin/env python3

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

import http
import ipaddress
import os
import socket
import urllib.parse
from common.secret import deobfuscate_json
from common.secret import obfuscate_json
from entity import Article
from entity import Folder
from entity import Subscription
from datetime import datetime
from flask_login import current_user
from io import BytesIO
from dao import Connection
from dao import Database
from tasks.actions import ActionError
from tasks.articles import articles_remove_tag
from tasks.articles import subs_mark_read_by_folder
from tasks.articles import subs_mark_read_by_sub
from tasks.articles import subs_mark_read_by_user
from tasks.subscriptions import subs_import
from tasks.subscriptions import subs_subscribe_url
from web.ext_type import requests
from web.ext_type import responses
import flask
import flask_login
import flask_socketio
import logging
import os.path
import port
import re
import tasks.actions as actions
import tempfile
import tomllib
import version
import web.ext_type.objects as ext_objs

app = flask.Flask(__name__)
app.config.from_file("../config.toml", load=tomllib.load, text=False)
app.config.from_prefixed_env("GROUCH")

app.jinja_env.globals["app_version"] = version.VERSION_FULL

socketio = flask_socketio.SocketIO(app, async_mode='gevent',
    cors_allowed_origins=app.config.get('CORS_ALLOWED_ORIGINS', '*'),
    message_queue=app.config['REDIS_URL'])

login_manager = flask_login.LoginManager()
login_manager.login_view = "/login"
login_manager.init_app(app)

FEED_SYNC_TIMEOUT_SECS = 600 # 10 min
UPLOAD_ALLOWED_TYPES = [ ".xml" ]
REGEX_REDIRECT_URL = re.compile(r"^(/\w+)+|/$")

def _action_error_response(e: ActionError):
    app.logger.error(e.message)
    match e.code:
        case ActionError.UNAUTHORIZED:
            return ext_objs.Error("Unauthorized", http.HTTPStatus.FORBIDDEN).as_dict()
        case ActionError.NOT_FOUND:
            return ext_objs.Error("Not found", http.HTTPStatus.NOT_FOUND).as_dict()
        case ActionError.SERVER_ERROR:
            return ext_objs.Error("An error occurred", http.HTTPStatus.INTERNAL_SERVER_ERROR).as_dict()
        case _:
            return ext_objs.Error(e.message, http.HTTPStatus.BAD_REQUEST).as_dict()


def _is_safe_url(url: str) -> bool:
    """Return True only if the URL uses http/https and resolves to a public IP address."""
    try:
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return False
        hostname = parsed.hostname
        if not hostname:
            return False
        for _, _, _, _, sockaddr in socket.getaddrinfo(hostname, None):
            addr = ipaddress.ip_address(sockaddr[0])
            if (addr.is_loopback or addr.is_private
                    or addr.is_link_local or addr.is_multicast
                    or addr.is_reserved or addr.is_unspecified):
                return False
        return True
    except Exception:
        return False

@login_manager.user_loader
def load_user(user_id):
    return ext_objs.User(user=stores.users.find_by_id(user_id))

@app.get("/login")
def login_get():
    return flask.render_template(
        "login.html",
        block_new_accounts=app.config.get("BLOCK_NEW_ACCOUNTS", False),
    )

@app.post("/login")
def login_post():
    arg = requests.LoginRequest(flask.request.form)

    try:
        arg.validate()
    except requests.ValidationException as e:
        app.logger.error(e.message)
        flask.flash(e.message)
        return flask.render_template(
            "login.html",
            arg=arg,
        )

    try:
        user = actions.users_authenticate(
            stores,
            current_user.get_id(),
            arg.username,
            arg.password
        )
    except ActionError as e:
        app.logger.error(e.message)
        flask.flash("Username or password incorrect")
        return flask.render_template(
            "login.html",
            arg=arg,
            block_new_accounts=app.config.get("BLOCK_NEW_ACCOUNTS", False),
        )

    flask.session.permanent = True
    flask_login.utils.login_user(ext_objs.User(user))

    if next := flask.request.args.get("next"):
        if not REGEX_REDIRECT_URL.fullmatch(next):
            logging.warn(f"{next} is not a valid redirection URL")
            next = None

    return flask.redirect(next or flask.url_for("index"))

@app.get("/logout")
@flask_login.login_required
def logout():
    flask_login.logout_user()
    return flask.redirect(flask.url_for("login_get"))

@app.get("/create_account")
def create_account_get():
    if app.config.get("BLOCK_NEW_ACCOUNTS", False):
        app.logger.error(f"Account creation is not available")
        flask.flash("Account creation is not available")
        return flask.redirect(flask.url_for("login_get"))
    return flask.render_template(
        "create_account.html",
    )

@app.post("/create_account")
def create_account_post():
    if app.config.get("BLOCK_NEW_ACCOUNTS", False):
        app.logger.error(f"Account creation is not available")
        flask.flash("Account creation is not available")
        return flask.redirect(flask.url_for("create_account_get"))

    arg = requests.CreateAccountRequest(flask.request.form)

    try:
        arg.validate()
    except requests.ValidationException as e:
        app.logger.error(e.message)
        flask.flash(e.message)
        return flask.render_template(
            "create_account.html",
            arg=arg,
        )

    try:
        user = actions.users_create_user(
            stores,
            None,
            arg.username,
            arg.email_address,
            arg.password,
        )
    except ActionError as e:
        app.logger.error(e.message)
        flask.flash("Duplicate username or email address")
        return flask.render_template(
            "create_account.html",
            arg=arg,
        )

    flask.flash(f"Account '{user.username}' created successfully", "success")
    return flask.redirect(flask.url_for("login_get"))

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
        if (owner_id := Folder.extract_owner_id(arg.folder)) != current_user.id:
            app.logger.error(f"Unauthorized folder ({owner_id}!={current_user.id})")
            return ext_objs.Error("Unauthorized").as_dict(), 403
        unread_only = arg.prop == Article.PROP_UNREAD
        articles, next_start = stores.articles.get_page_by_folder(arg.folder, start, unread_only=unread_only)
    elif arg.sub:
        if (owner_id := Subscription.extract_owner_id(arg.sub)) != current_user.id:
            app.logger.error(f"Unauthorized sub ({owner_id}!={current_user.id})")
            return ext_objs.Error("Unauthorized").as_dict(), 403
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
        title=f"{current_user.username} subscriptions in Grouch",
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
        return ext_objs.Error("Invalid request").as_dict()
    elif not arg.url:
        app.logger.error(f"Missing URL")
        return ext_objs.Error("Missing URL").as_dict()
    elif not _is_safe_url(arg.url):
        app.logger.error(f"Rejected unsafe URL: {arg.url}")
        return ext_objs.Error("Invalid URL").as_dict()

    subs_subscribe_url.delay(current_user.id, arg.url, notify=True)

    return responses.SubscribeResponse().as_dict()

@app.post("/setProperty")
@flask_login.login_required
def set_property():
    if not (arg := requests.SetPropertyRequest(flask.request.json)):
        app.logger.error(f"Empty request")
        return ext_objs.Error("Invalid request").as_dict()

    try:
        article = actions.articles_set_property(
            stores,
            current_user.id,
            arg.article_id,
            arg.prop_name,
            arg.is_set,
        )
    except ActionError as e:
        return _action_error_response(e)

    return article.props

@app.post("/rename")
@flask_login.login_required
def rename():
    if not (arg := requests.RenameRequest(flask.request.json)):
        app.logger.error(f"Empty request")
        return ext_objs.Error("Invalid request").as_dict()

    try:
        actions.objects_rename(
            stores,
            current_user.id,
            arg.id,
            arg.title,
        )
    except ActionError as e:
        return _action_error_response(e)

    return responses.RenameResponse(
        toc=_fetch_table_of_contents(),
    ).as_dict()

@app.post("/setTags")
@flask_login.login_required
def set_tags():
    if not (arg := requests.SetTagsRequest(flask.request.json)):
        app.logger.error(f"Empty request")
        return ext_objs.Error("Invalid request").as_dict()

    try:
        article = actions.articles_set_tags(
            stores,
            current_user.id,
            arg.article_id,
            arg.tags,
        )
    except ActionError as e:
        return _action_error_response(e)

    return responses.SetTagsResponse(
        toc=_fetch_table_of_contents(),
        tags=article.tags,
    ).as_dict()

@app.post("/createFolder")
@flask_login.login_required
def create_folder():
    if not (arg := requests.CreateFolderRequest(flask.request.json)):
        app.logger.error(f"Empty request")
        return ext_objs.Error("Invalid request").as_dict()

    try:
        actions.folders_create(
            stores,
            current_user.id,
            arg.title,
        )
    except ActionError as e:
        return _action_error_response(e)

    return responses.CreateFolderResponse(
        toc=_fetch_table_of_contents(),
    ).as_dict()

@app.post("/moveSub")
@flask_login.login_required
def move_sub():
    if not (arg := requests.MoveSubRequest(flask.request.json)):
        app.logger.error(f"Empty request")
        return ext_objs.Error("Invalid request").as_dict()

    try:
        actions.subs_move(
            stores,
            current_user.id,
            arg.id,
            arg.destination,
        )
    except ActionError as e:
        return _action_error_response(e)

    return responses.MoveSubResponse(
        toc=_fetch_table_of_contents(),
    ).as_dict()

@app.post("/removeTag")
@flask_login.login_required
def remove_tag():
    arg = requests.RemoveTagRequest(flask.request.json)
    if not arg:
        app.logger.error(f"Empty request")
        return ext_objs.Error("Invalid request").as_dict()
    elif not arg.tag:
        app.logger.error(f"Missing tag")
        return ext_objs.Error("Missing tag").as_dict()

    articles_remove_tag.delay(current_user.id, arg.tag)

    # Remove it from the list manually
    toc = _fetch_table_of_contents()
    toc.remove_tag(arg.tag)

    return responses.MoveSubResponse(toc).as_dict()

@app.post("/unsubscribe")
@flask_login.login_required
def unsubscribe():
    if not (arg := requests.UnsubscribeRequest(flask.request.json)):
        app.logger.error(f"Empty request")
        return ext_objs.Error("Invalid request").as_dict()

    try:
        actions.subs_unsubscribe(
            stores,
            current_user.id,
            arg.id,
        )
    except ActionError as e:
        return _action_error_response(e)

    # Actual deletion will happen asynchronously
    toc = _fetch_table_of_contents()
    toc.remove_subscription(arg.id)

    return responses.UnsubscribeResponse(toc).as_dict()

@app.post("/deleteFolder")
@flask_login.login_required
def delete_folder():
    if not (arg := requests.DeleteFolderRequest(flask.request.json)):
        app.logger.error(f"Empty request")
        return ext_objs.Error("Invalid request").as_dict()

    try:
        actions.folders_delete(
            stores,
            current_user.id,
            arg.id,
        )
    except ActionError as e:
        return _action_error_response(e)

    # Actual deletion will happen asynchronously
    toc = _fetch_table_of_contents()
    toc.remove_folder(arg.id)

    return responses.DeleteFolderResponse(toc).as_dict()

@app.post("/markAllAsRead")
@flask_login.login_required
def mark_all_as_read():
    if not (arg := requests.MarkAllAsReadRequest(flask.request.json)):
        app.logger.error(f"Empty request")
        return ext_objs.Error("Invalid request").as_dict()

    match arg.scope:
        case requests.MarkAllAsReadRequest.SCOPE_ALL:
            subs_mark_read_by_user.delay(current_user.id)
        case requests.MarkAllAsReadRequest.SCOPE_FOLDER:
            if not arg.id:
                app.logger.error(f"Missing id")
                return ext_objs.Error("Missing id").as_dict()
            elif (owner_id := Folder.extract_owner_id(arg.id)) != current_user.id:
                app.logger.error(f"Unauthorized object ({owner_id}!={current_user.id})")
                return ext_objs.Error("Unauthorized", http.HTTPStatus.FORBIDDEN).as_dict()

            subs_mark_read_by_folder.delay(current_user.id, arg.id)
        case requests.MarkAllAsReadRequest.SCOPE_SUB:
            if not arg.id:
                app.logger.error(f"Missing id")
                return ext_objs.Error("Missing id").as_dict()
            elif (owner_id := Subscription.extract_owner_id(arg.id)) != current_user.id:
                app.logger.error(f"Unauthorized object ({owner_id}!={current_user.id})")
                return ext_objs.Error("Unauthorized", http.HTTPStatus.FORBIDDEN).as_dict()

            subs_mark_read_by_sub.delay(current_user.id, arg.id)

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
        next_sync = actions.subs_sync(
            stores,
            current_user.id,
            datetime.now(),
            FEED_SYNC_TIMEOUT_SECS,
        )
    except ActionError as e:
        return _action_error_response(e)

    return responses.SyncFeedsResponse(
        next_sync=next_sync.isoformat(),
    ).as_dict()

@app.post("/importFeeds")
@flask_login.login_required
def import_feeds():
    # Check individual files
    if "file" not in flask.request.files:
        app.logger.error(f"No file in request")
        return ext_objs.Error("No file provided").as_dict()

    if not (file := flask.request.files["file"]) or file.filename == "":
        app.logger.error(f"No filename in file")
        return ext_objs.Error("Invalid request").as_dict()

    _, ext = os.path.splitext(file.filename)
    if ext not in UPLOAD_ALLOWED_TYPES:
        app.logger.error(f"Unsupported file type: '{ext}'")
        return ext_objs.Error("Unsupported file type").as_dict()

    with tempfile.TemporaryFile() as tmp:
        file.save(tmp)
        tmp.seek(0)

        doc = port.import_opml(tmp)

    if not doc:
        app.logger.error(f"Unable to import document")
        return ext_objs.Error("An error occurred", http.HTTPStatus.INTERNAL_SERVER_ERROR).as_dict()

    subs_import.delay(current_user.id, doc.to_dict(), notify=True)

    return responses.ImportFeedsResponse().as_dict()

@socketio.on("connect")
def socketio_connect():
    if not current_user.is_authenticated:
        logging.warning("Unauthenticated user")
        return False

    flask_socketio.join_room(current_user.id)
    app.logger.debug(f"Connected; joined {current_user.id}")

@socketio.on("disconnect")
def socketio_disconnect():
    flask_socketio.leave_room(current_user.id)
    app.logger.debug("Disconnected")

def _fetch_table_of_contents() -> ext_objs.TableOfContents:
    subs = stores.subs.find_by_user(current_user.id)
    unread_counts = stores.subs.get_unread_counts_by_user(current_user.id)
    feeds = stores.feeds.find_by_id(*[sub.feed_id for sub in subs])
    folders = stores.folders.find_by_user(current_user.id)
    feed_map = { feed.id:feed for feed in feeds }
    tags = stores.articles.find_tags_by_user(current_user.id)

    return ext_objs.TableOfContents(
        subs=[ext_objs.Subscription(
            sub,
            feed_map[sub.feed_id],
            unread_counts.get(sub.id),
        ) for sub in subs],
        folders=[ext_objs.Folder(folder) for folder in folders],
        tags=[ext_objs.Tag(tag) for tag in tags],
    )

def init_app():
    logging.basicConfig(level=logging.DEBUG)

    if not app.config.get('CORS_ALLOWED_ORIGINS'):
        logging.warning(
            "CORS_ALLOWED_ORIGINS is not set; defaulting to '*'. "
            "Set CORS_ALLOWED_ORIGINS in config.toml for production."
        )

    global stores
    conn = Connection()
    conn.connect(
        app.config["DATABASE_NAME"],
        app.config["DATABASE_USERNAME"],
        app.config["DATABASE_PASSWORD"],
        app.config["DATABASE_HOST"],
        app.config["DATABASE_PORT"],
        use_tls=app.config.get("DATABASE_USE_TLS", False),
    )
    stores = Database(conn.db)

init_app()

if __name__ == "__main__":
    socketio.run(app, host='0.0.0.0', port='8080',
                 debug=os.environ.get('FLASK_DEBUG', '0') == '1')
