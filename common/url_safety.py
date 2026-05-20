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

import ipaddress
import logging
import socket
import urllib.parse

import requests

URLHAUS_CHECK_TIMEOUT_SECS = 5
_URLHAUS_API_URL = "https://urlhaus-api.abuse.ch/v1/url/"


def is_safe_url(url: str) -> bool:
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


def check_url_remote(url: str, config: dict) -> bool:
    """Run all configured remote malware/blocklist checks against url.

    Returns True if every enabled check passes (URL is safe to proceed),
    False if any check rejects it. Checks that have no API key configured
    are skipped with a warning rather than failing closed — you cannot
    check without credentials. All other error conditions (timeout, network
    failure, unexpected response) are fail-closed.

    Additional remote services can be wired in here as new private helpers.
    """
    if not _check_urlhaus(url, config.get("URLHAUS_API_KEY")):
        return False
    return True


def _check_urlhaus(url: str, api_key: str | None) -> bool:
    """Check url against the URLhaus malware database (abuse.ch).

    Returns True if the URL is not found in URLhaus (safe to proceed).
    """
    if not api_key:
        logging.warning(f"URLHAUS_API_KEY not configured; skipping URLhaus check for {url}")
        return True

    try:
        response = requests.post(
            _URLHAUS_API_URL,
            data={"url": url},
            headers={"Auth-Key": api_key},
            timeout=URLHAUS_CHECK_TIMEOUT_SECS,
        )
        data = response.json()
    except requests.exceptions.Timeout:
        logging.error(f"URLhaus check timed out for {url}; rejecting")
        return False
    except Exception as e:
        logging.error(f"URLhaus check failed for {url}: {e}; rejecting")
        return False

    status = data.get("query_status")

    if status == "no_results":
        return True

    if status == "ok":
        bl = data.get("blacklists") or {}
        logging.warning(
            f"URLhaus rejected URL: {url} | "
            f"url_status={data.get('url_status')} "
            f"threat={data.get('threat')} "
            f"host={data.get('host')} "
            f"date_added={data.get('date_added')} "
            f"tags={data.get('tags')} "
            f"spamhaus_dbl={bl.get('spamhaus_dbl')} "
            f"surbl={bl.get('surbl')} "
            f"ref={data.get('urlhaus_reference')}"
        )
        return False

    logging.error(f"Unexpected URLhaus query_status={status!r} for {url}; rejecting")
    return False
