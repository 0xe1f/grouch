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

from tasks.actions import ActionError
from web.ext_type import requests
import flask
import flask_login
import logging
import re
import tasks.actions as actions
import web.ext_type.objects as ext_objs

bp = flask.Blueprint("users", __name__)

REGEX_REDIRECT_URL = re.compile(r"^(/\w+)+|/$")

@bp.get("/login")
def login_get():
    return flask.render_template(
        "login.html",
        block_new_accounts=flask.current_app.config.get("BLOCK_NEW_ACCOUNTS", False),
    )

@bp.post("/login")
def login_post():
    arg = requests.LoginRequest(flask.request.form)

    try:
        arg.validate()
    except requests.ValidationException as e:
        flask.current_app.logger.error(e.message)
        flask.flash(e.message)
        return flask.render_template(
            "login.html",
            arg=arg,
        )

    stores = flask.current_app.extensions['stores']
    try:
        user = actions.users_authenticate(
            stores,
            flask_login.current_user.get_id(),
            arg.username,
            arg.password
        )
    except ActionError as e:
        flask.current_app.logger.error(e.message)
        flask.flash("Username or password incorrect")
        return flask.render_template(
            "login.html",
            arg=arg,
            block_new_accounts=flask.current_app.config.get("BLOCK_NEW_ACCOUNTS", False),
        )

    flask.session.permanent = True
    flask_login.utils.login_user(ext_objs.User(user))

    if next := flask.request.args.get("next"):
        if not REGEX_REDIRECT_URL.fullmatch(next):
            logging.warn(f"{next} is not a valid redirection URL")
            next = None

    return flask.redirect(next or flask.url_for("index"))

@bp.get("/logout")
@flask_login.login_required
def logout():
    flask_login.logout_user()
    return flask.redirect(flask.url_for("users.login_get"))

@bp.get("/create_account")
def create_account_get():
    if flask.current_app.config.get("BLOCK_NEW_ACCOUNTS", False):
        flask.current_app.logger.error(f"Account creation is not available")
        flask.flash("Account creation is not available")
        return flask.redirect(flask.url_for("users.login_get"))
    return flask.render_template(
        "create_account.html",
    )

@bp.post("/create_account")
def create_account_post():
    if flask.current_app.config.get("BLOCK_NEW_ACCOUNTS", False):
        flask.current_app.logger.error(f"Account creation is not available")
        flask.flash("Account creation is not available")
        return flask.redirect(flask.url_for("users.create_account_get"))

    arg = requests.CreateAccountRequest(flask.request.form)

    try:
        arg.validate()
    except requests.ValidationException as e:
        flask.current_app.logger.error(e.message)
        flask.flash(e.message)
        return flask.render_template(
            "create_account.html",
            arg=arg,
        )

    stores = flask.current_app.extensions['stores']
    try:
        user = actions.users_create_user(
            stores,
            None,
            arg.username,
            arg.email_address,
            arg.password,
        )
    except ActionError as e:
        flask.current_app.logger.error(e.message)
        flask.flash("Duplicate username or email address")
        return flask.render_template(
            "create_account.html",
            arg=arg,
        )

    flask.flash(f"Account '{user.username}' created successfully", "success")
    return flask.redirect(flask.url_for("users.login_get"))
