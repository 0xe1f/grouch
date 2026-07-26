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

"""Discover and normalize feed favicons."""

from __future__ import annotations

from common.url_safety import is_safe_url
from dataclasses import dataclass
from html.parser import HTMLParser
from io import BytesIO
from urllib.parse import urljoin
from urllib.parse import urlparse
import base64
import hashlib
import ipaddress
import logging
import re

import requests
from PIL import Image

try:
    import cairosvg
except ImportError:  # pragma: no cover
    cairosvg = None

DISPLAY_SIZE = 60
MAX_BYTES = 1_048_576
MAX_EDGE = 512
MIN_BYTES = 16
FETCH_TIMEOUT_SECS = 10
USER_AGENT = "GrouchFavicon/1.0 (+https://github.com/grouch-reader/grouch)"

_ICON_RELS = {
    "icon",
    "shortcut icon",
    "apple-touch-icon",
    "apple-touch-icon-precomposed",
}

_FEEDISH_PATH = re.compile(
    r"/(feed|rss|atom)(/|$)|rss\.xml|atom\.xml|feed\.xml|feed\.rss|newsfeed|rssfeed",
    re.I,
)


@dataclass
class FaviconSource:
    data: bytes
    content_type: str
    source_url: str


@dataclass
class DisplayImage:
    png: bytes
    width: int
    height: int
    content_hash: str


def hash_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def build_display_png(data: bytes, content_type: str | None = None) -> DisplayImage | None:
    """Convert source bytes to a serve PNG (no upscale; vectors at DISPLAY_SIZE)."""
    ctype = (content_type or "").split(";")[0].strip().lower()
    try:
        if ctype == "image/svg+xml" or _looks_like_svg(data):
            image = _rasterize_svg(data)
        else:
            image = _open_raster(data)
        if image is None:
            return None
        image = _normalize_mode(image)
        if max(image.size) > MAX_EDGE:
            return None
        image = _fit_display(image)
        buf = BytesIO()
        image.save(buf, format="PNG")
        png = buf.getvalue()
        w, h = image.size
        return DisplayImage(png=png, width=w, height=h, content_hash=hash_bytes(png))
    except Exception as e:
        logging.debug("Failed to build display PNG: %s", e)
        return None


def discover_favicon(site_url: str | None, feed_url: str | None = None) -> FaviconSource | None:
    """Fetch and return the best favicon for a feed's site."""
    bases = []
    for url in (site_url, feed_url):
        if url and url not in bases:
            bases.append(url)

    for base in bases:
        found = _discover_from_base(base)
        if found:
            return found
    return None


def _discover_from_base(base_url: str) -> FaviconSource | None:
    html_url = base_url
    html = _fetch_bytes(html_url, accept="text/html,*/*")
    final_html_url = html_url

    if html and not _looks_like_html(html.data, html.content_type):
        html = None

    if html is None or _path_looks_feedish(base_url):
        origin = _origin(base_url)
        if origin and origin.rstrip("/") != base_url.rstrip("/"):
            alt = _fetch_bytes(origin, accept="text/html,*/*")
            if alt and _looks_like_html(alt.data, alt.content_type):
                html = alt
                final_html_url = alt.source_url or origin

    candidates: list[tuple[int, str, str | None]] = []
    if html:
        for rel, href, typ, sizes in _parse_icon_links(html.data):
            abs_url = urljoin(final_html_url, href)
            candidates.append((_candidate_rank(rel, sizes), abs_url, typ))
        candidates.sort(key=lambda c: c[0])

    seen = set()
    for _, href, typ in candidates:
        if href in seen:
            continue
        seen.add(href)
        source = _materialize(href, declared_type=typ)
        if source and build_display_png(source.data, source.content_type):
            return source

    origin = _origin(final_html_url or base_url)
    if origin:
        ico = f"{origin.rstrip('/')}/favicon.ico"
        if ico not in seen:
            source = _materialize(ico, declared_type="image/x-icon")
            if source and build_display_png(source.data, source.content_type):
                return source
    return None


def _materialize(href: str, declared_type: str | None = None) -> FaviconSource | None:
    if href.lower().startswith("data:"):
        return _parse_data_url(href)
    if not href.lower().startswith(("http://", "https://")):
        return None
    if not _is_safe_fetch_url(href):
        return None
    fetched = _fetch_bytes(href)
    if not fetched:
        return None
    ctype = _pick_content_type(fetched.content_type, declared_type, fetched.data)
    if not _acceptable_payload(fetched.data, ctype):
        return None
    return FaviconSource(data=fetched.data, content_type=ctype, source_url=fetched.source_url)


@dataclass
class _Fetched:
    data: bytes
    content_type: str
    source_url: str


def _fetch_bytes(url: str, accept: str = "*/*") -> _Fetched | None:
    if not _is_safe_fetch_url(url):
        return None
    try:
        response = requests.get(
            url,
            timeout=FETCH_TIMEOUT_SECS,
            headers={"User-Agent": USER_AGENT, "Accept": accept},
            allow_redirects=True,
        )
    except requests.exceptions.RequestException as e:
        logging.debug("Favicon fetch failed for %s: %s", url, e)
        return None

    if response.status_code != 200:
        return None
    # Re-check final URL after redirects
    if not _is_safe_fetch_url(response.url):
        return None
    data = response.content or b""
    if len(data) > MAX_BYTES or len(data) < MIN_BYTES:
        return None
    ctype = (response.headers.get("Content-Type") or "").split(";")[0].strip().lower()
    return _Fetched(data=data, content_type=ctype, source_url=response.url)


def _is_safe_fetch_url(url: str) -> bool:
    """Like is_safe_url but also reject literal private IPs in the URL host."""
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https") or not parsed.hostname:
            return False
        host = parsed.hostname
        try:
            addr = ipaddress.ip_address(host)
            if (addr.is_loopback or addr.is_private or addr.is_link_local
                    or addr.is_multicast or addr.is_reserved or addr.is_unspecified):
                return False
            return True
        except ValueError:
            pass
        return is_safe_url(url)
    except Exception:
        return False


def _parse_data_url(url: str) -> FaviconSource | None:
    # data:[<mediatype>][;base64],<data>
    try:
        header, payload = url.split(",", 1)
    except ValueError:
        return None
    meta = header[5:]  # strip data:
    parts = meta.split(";") if meta else []
    mime = parts[0] if parts and parts[0] else "application/octet-stream"
    is_b64 = any(p.lower() == "base64" for p in parts[1:])
    try:
        if is_b64:
            data = base64.b64decode(payload)
        else:
            from urllib.parse import unquote_to_bytes
            data = unquote_to_bytes(payload)
    except Exception:
        return None
    ctype = _pick_content_type(mime, None, data)
    if not _acceptable_payload(data, ctype):
        return None
    return FaviconSource(data=data, content_type=ctype, source_url=url[:64] + ("…" if len(url) > 64 else ""))


class _IconLinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.icons: list[tuple[str, str, str, str]] = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() != "link":
            return
        ad = {k.lower(): (v or "") for k, v in attrs}
        rel = ad.get("rel", "").lower().strip()
        href = ad.get("href", "").strip()
        if not href or rel not in _ICON_RELS:
            return
        self.icons.append((rel, href, ad.get("type", ""), ad.get("sizes", "")))


def _parse_icon_links(html: bytes) -> list[tuple[str, str, str, str]]:
    text = html.decode("utf-8", errors="ignore")
    parser = _IconLinkParser()
    try:
        parser.feed(text)
    except Exception:
        pass
    return parser.icons


def _candidate_rank(rel: str, sizes: str) -> int:
    # Lower is better
    rel_score = 0 if rel == "icon" else 1 if "apple" in rel else 2
    size_score = 2
    if sizes and sizes.lower() != "any":
        nums = [int(x) for x in re.findall(r"\d+", sizes)]
        if nums:
            best = max(nums)
            if best >= DISPLAY_SIZE:
                size_score = 0
            else:
                size_score = 1
    return rel_score * 10 + size_score


def _path_looks_feedish(url: str) -> bool:
    path = urlparse(url).path or ""
    return bool(_FEEDISH_PATH.search(path))


def _origin(url: str) -> str | None:
    p = urlparse(url)
    if not p.scheme or not p.netloc:
        return None
    return f"{p.scheme}://{p.netloc}"


def _looks_like_html(data: bytes, content_type: str) -> bool:
    if "html" in (content_type or "").lower():
        return True
    head = data.lstrip()[:200].lower()
    return head.startswith(b"<!doctype") or head.startswith(b"<html") or b"<html" in head


def _looks_like_svg(data: bytes) -> bool:
    head = data.lstrip()[:200].lower()
    return head.startswith(b"<svg") or (head.startswith(b"<?xml") and b"<svg" in data[:1000].lower())


def _pick_content_type(header: str | None, declared: str | None, data: bytes) -> str:
    for candidate in (header, declared):
        if candidate and candidate.lower().startswith("image/"):
            return candidate.split(";")[0].strip().lower()
    sniffed = _sniff_type(data)
    if sniffed:
        return sniffed
    return (header or declared or "application/octet-stream").split(";")[0].strip().lower()


def _sniff_type(data: bytes) -> str | None:
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    if data[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    if data[:6] in (b"GIF87a", b"GIF89a"):
        return "image/gif"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    if len(data) >= 4 and data[:4] in (b"\x00\x00\x01\x00", b"\x00\x00\x02\x00"):
        return "image/x-icon"
    if _looks_like_svg(data):
        return "image/svg+xml"
    return None


def _acceptable_payload(data: bytes, content_type: str) -> bool:
    if len(data) < MIN_BYTES or len(data) > MAX_BYTES:
        return False
    if content_type.startswith("image/") or _sniff_type(data):
        # Reject obvious HTML error pages mislabeled as images
        if _looks_like_html(data, "") and not _looks_like_svg(data):
            return False
        return True
    return False


def _open_raster(data: bytes) -> Image.Image | None:
    img = Image.open(BytesIO(data))
    img.load()
    # Multi-frame ICO/GIF: pick best frame
    if getattr(img, "n_frames", 1) > 1 and img.format == "ICO":
        best = None
        best_score = -1
        for i in range(img.n_frames):
            img.seek(i)
            frame = img.copy()
            w, h = frame.size
            if max(w, h) > MAX_EDGE:
                continue
            # Prefer >= DISPLAY_SIZE, else largest
            score = (1_000_000 + w * h) if min(w, h) >= DISPLAY_SIZE else w * h
            if score > best_score:
                best_score = score
                best = frame
        return best
    if getattr(img, "is_animated", False):
        img.seek(0)
    return img.copy()


def _rasterize_svg(data: bytes) -> Image.Image | None:
    if cairosvg is None:
        logging.debug("cairosvg not available; skipping SVG favicon")
        return None
    png = cairosvg.svg2png(
        bytestring=data,
        output_width=DISPLAY_SIZE,
        output_height=DISPLAY_SIZE,
    )
    return Image.open(BytesIO(png)).convert("RGBA")


def _normalize_mode(image: Image.Image) -> Image.Image:
    if image.mode in ("RGBA", "RGB"):
        return image
    if image.mode == "P":
        return image.convert("RGBA")
    if image.mode == "LA":
        return image.convert("RGBA")
    return image.convert("RGBA")


def _fit_display(image: Image.Image) -> Image.Image:
    w, h = image.size
    if w <= DISPLAY_SIZE and h <= DISPLAY_SIZE:
        return image
    image = image.copy()
    image.thumbnail((DISPLAY_SIZE, DISPLAY_SIZE), Image.Resampling.LANCZOS)
    tw, th = image.size
    if tw == DISPLAY_SIZE and th == DISPLAY_SIZE:
        return image
    canvas = Image.new("RGBA", (DISPLAY_SIZE, DISPLAY_SIZE), (0, 0, 0, 0))
    canvas.paste(image, ((DISPLAY_SIZE - tw) // 2, (DISPLAY_SIZE - th) // 2), image if image.mode == "RGBA" else None)
    return canvas
