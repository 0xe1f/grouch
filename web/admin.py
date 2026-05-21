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

from flask_login import current_user
from parser.parse import parse_url
from web.auth import roles_required
import flask
import flask_login
import json
import logging
import urllib.request

bp = flask.Blueprint("admin", __name__, url_prefix="/admin")

def get_menu_items():
    return [
        {
            "endpoint": "admin.test_access",
            "title": "Test Access",
            "class_name": "test-access",
        },
    ]

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
