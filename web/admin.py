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
from flask_login import current_user
from parser.parse import parse_url
from tasks.actions import ActionError
from tasks.actions import invites_cancel
from tasks.actions import invites_resend
from tasks.actions import invites_send
from web.auth import roles_required
from web.ext_type.requests import SendInviteRequest
from web.ext_type.objects import ValidationException
import flask
import flask_login
import json
import logging
import urllib.request

bp = flask.Blueprint("admin", __name__, url_prefix="/admin")

PAGE_SIZE = 40

def get_menu_items():
    return [
        {
            "endpoint": "admin.invitations",
            "title": "Invitations",
            "class_name": "invitations",
        },
        {
            "endpoint": "admin.test_access",
            "title": "Test Access",
            "class_name": "test-access",
        },
    ]


def _get_stores():
    return flask.current_app.extensions["stores"]

@bp.before_request
@flask_login.login_required
@roles_required("admin")
def check_admin():
    pass

@bp.get("/")
def index():
    default_endpoint = get_menu_items()[0]["endpoint"]
    return flask.redirect(flask.url_for(default_endpoint))

@bp.get("/test-access")
def test_access():
    return flask.render_template(
        "admin/test_access.html",
        menu_items=get_menu_items(),
        active_endpoint=flask.request.endpoint
    )

@bp.get("/invitations")
def invitations():
    stores = _get_stores()

    status_filter = flask.request.args.get("status", "pending")
    email_find = (flask.request.args.get("email") or "").strip() or None
    raw_start = flask.request.args.get("start")
    is_partial = flask.request.args.get("partial") == "1"

    start = deobfuscate_json(raw_start) if raw_start else None

    if email_find:
        invites = stores.invites.find_by_invitee_email(email_find)
        invites.sort(key=lambda i: i.sent_at or 0, reverse=True)
        next_start = None
    elif status_filter == "all":
        invites, raw_next = stores.invites.get_page_all(start=start, limit=PAGE_SIZE)
        next_start = obfuscate_json(raw_next) if raw_next is not None else None
    else:
        if status_filter not in ("pending", "expired", "cancelled", "accepted"):
            status_filter = "pending"
        invites, raw_next = stores.invites.get_page_by_status(
            status_filter, start=start, limit=PAGE_SIZE
        )
        next_start = obfuscate_json(raw_next) if raw_next is not None else None

    if is_partial:
        rows_html = flask.render_template(
            "admin/invitations_rows.html",
            invites=invites,
        )
        return flask.jsonify(rows_html=rows_html, next_start=next_start)

    return flask.render_template(
        "admin/invitations.html",
        invites=invites,
        status_filter=status_filter,
        email_find=email_find,
        send_email=flask.request.args.get("send_email"),
        next_start=next_start,
        menu_items=get_menu_items(),
        active_endpoint=flask.request.endpoint,
    )


@bp.post("/invitations/send")
def invitations_send():
    stores = _get_stores()

    try:
        req = SendInviteRequest(flask.request.form)
        req.validate()
    except ValidationException as e:
        flask.flash(str(e), "error")
        return flask.redirect(flask.url_for("admin.invitations"))

    expiry_days = flask.current_app.config.get("INVITE_EXPIRY_DAYS", 14)
    try:
        expiry_days = int(expiry_days)
    except (TypeError, ValueError):
        expiry_days = 14

    try:
        invites_send(stores, current_user.id, req.email, expiry_days=expiry_days)
        flask.flash(f"Invitation sent to {req.email}.", "success")
    except ActionError as e:
        flask.flash(e.message, "error")

    return flask.redirect(flask.url_for("admin.invitations"))


@bp.post("/invitations/cancel")
def invitations_cancel():
    stores = _get_stores()
    invite_id = flask.request.form.get("invite_id", "").strip()

    try:
        invites_cancel(stores, invite_id)
        flask.flash("Invitation cancelled.", "success")
    except ActionError as e:
        flask.flash(e.message, "error")

    return flask.redirect(flask.url_for("admin.invitations"))


@bp.post("/invitations/resend")
def invitations_resend():
    stores = _get_stores()
    invite_id = flask.request.form.get("invite_id", "").strip()

    expiry_days = flask.current_app.config.get("INVITE_EXPIRY_DAYS", 14)
    try:
        expiry_days = int(expiry_days)
    except (TypeError, ValueError):
        expiry_days = 14

    try:
        invites_resend(stores, invite_id, current_user.id, expiry_days=expiry_days)
        flask.flash("Invitation resent.", "success")
    except ActionError as e:
        flask.flash(e.message, "error")

    return flask.redirect(flask.url_for("admin.invitations"))


@bp.post("/test-access")
def test_access_post():
    url = flask.request.form.get("url", "").strip()
    raw_text = ""
    feed_details = ""

    if url:
        try:
            with urllib.request.urlopen(url, timeout=15) as resp:
                status = resp.status
                headers = dict(resp.headers)
                body = resp.read().decode("utf-8", errors="replace")
            raw_text = f"HTTP {status}\n\n"
            raw_text += "\n".join(f"{k}: {v}" for k, v in headers.items())
            raw_text += f"\n\n{body}"
        except Exception as e:
            raw_text = f"Error fetching URL: {e}"

        try:
            result = parse_url(url)
            if result is None:
                feed_details = "Parser returned no result."
            else:
                details = {"url": result.url}
                if result.feed:
                    details.update(result.feed.as_dict())
                    details["entries"] = [entry.as_dict() for entry in result.entries]
                if result.alternatives:
                    details["alternatives"] = result.alternatives
                if not result.feed and not result.alternatives:
                    details["error"] = "No feed or alternate URLs found."
                feed_details = json.dumps(details, indent=2, default=str)
        except Exception as e:
            feed_details = f"Error parsing feed: {e}"

    return flask.render_template(
        "admin/test_access.html",
        url=url,
        raw_text=raw_text,
        feed_details=feed_details,
        menu_items=get_menu_items(),
        active_endpoint="admin.test_access",
    )
