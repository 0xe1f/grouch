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
from tasks.actions import invites_mark_accepted
from tasks.actions import invites_validate
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
    if flask_login.current_user.is_authenticated:
        return flask.redirect(flask.url_for("index"))

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
    if flask_login.current_user.is_authenticated:
        return flask.redirect(flask.url_for("index"))

    stores = flask.current_app.extensions["stores"]
    token = flask.request.args.get("token", "").strip() or None

    if token:
        invite = stores.invites.find_by_token(token)
        import datetime
        from datetime import timezone
        now = datetime.datetime.now(tz=timezone.utc).timestamp()
        if (
            not invite
            or invite.status != "pending"
            or invite.expiry_date <= now
        ):
            flask.current_app.logger.error(f"Invitation is invalid or has expired: {invite.status} {invite.expiry_date} {now}")
            flask.flash("This invitation is invalid or has expired.")
            return flask.redirect(flask.url_for("users.login_get"))

        return flask.render_template(
            "create_account.html",
            invite_token=token,
            message_banner=(
                "You've been invited to create a Grouch Reader account. "
                "Fill in the details below to get started."
            ),
        )

    if flask.current_app.config.get("BLOCK_NEW_ACCOUNTS", False):
        flask.current_app.logger.error("Account creation is not available")
        flask.flash("Account creation is not available")
        return flask.redirect(flask.url_for("users.login_get"))

    return flask.render_template("create_account.html")


@bp.post("/create_account")
def create_account_post():
    stores = flask.current_app.extensions["stores"]
    token = flask.request.form.get("token", "").strip() or None

    if not token and flask.current_app.config.get("BLOCK_NEW_ACCOUNTS", False):
        flask.current_app.logger.error("Account creation is not available")
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
            invite_token=token,
        )

    invite = None
    if token:
        try:
            invite = invites_validate(stores, token, arg.email_address)
        except ActionError as e:
            flask.flash(e.message)
            return flask.render_template(
                "create_account.html",
                arg=arg,
                invite_token=token,
                message_banner=(
                    "You've been invited to create a Grouch Reader account. "
                    "Fill in the details below to get started."
                ),
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
        flask.current_app.logger.error(e.message)
        flask.flash("Duplicate username or email address")
        return flask.render_template(
            "create_account.html",
            arg=arg,
            invite_token=token,
        )

    if invite:
        invites_mark_accepted(stores, invite, user.id)

    flask.flash(f"Account '{user.username}' created successfully", "success")
    return flask.redirect(flask.url_for("users.login_get"))
