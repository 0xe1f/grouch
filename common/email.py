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

from datetime import datetime
from datetime import timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import flask
import logging
import smtplib

logger = logging.getLogger(__name__)


def send_invite(
    token: str,
    to_address: str,
    expiry_timestamp: float,
):
    """Render invite email templates and send via configured SMTP server.

    Must be called from within a Flask request or application context.
    """
    app = flask.current_app._get_current_object()

    accept_url = flask.url_for(
        "users.create_account_get",
        token=token,
        _external=True,
    )

    expiry_date_formatted = datetime.fromtimestamp(
        expiry_timestamp, tz=timezone.utc
    ).strftime("%B %d, %Y")

    text_body = flask.render_template(
        "email/invite.txt",
        accept_url=accept_url,
        expiry_date_formatted=expiry_date_formatted,
    )
    html_body = flask.render_template(
        "email/invite.html",
        accept_url=accept_url,
        expiry_date_formatted=expiry_date_formatted,
    )

    from_address = app.config.get("SMTP_FROM", "noreply@localhost")
    subject = "You've been invited to create a Grouch Reader account"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = from_address
    msg["To"] = to_address
    msg.attach(MIMEText(text_body, "plain"))
    msg.attach(MIMEText(html_body, "html"))

    host = app.config.get("SMTP_HOST", "localhost")
    port = int(app.config.get("SMTP_PORT", 587))
    use_tls = app.config.get("SMTP_TLS", True)
    user = app.config.get("SMTP_USER")
    password = app.config.get("SMTP_PASSWORD")

    if isinstance(use_tls, str):
        use_tls = use_tls.lower() not in ("false", "0", "no")

    logger.debug("Sending invite email to %s via %s:%d", to_address, host, port)

    with smtplib.SMTP(host, port) as smtp:
        if use_tls:
            smtp.starttls()
        if user and password:
            smtp.login(user, password)
        smtp.sendmail(from_address, to_address, msg.as_string())

    logger.info("Invite email sent to %s", to_address)
