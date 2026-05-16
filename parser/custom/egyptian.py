# Copyright (C) 2025 Akop Karapetyan
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

from entity import Entry
from entity import Feed
from parser import ParseResult
from parser import consts
from parser import sanitizer

from datetime import datetime
from dateutil.parser import isoparse
from html import escape
from json import loads
from urllib.parse import urljoin
from urllib.request import urlopen
import re

# This is a heuristic to avoid trash in the summary and unnecessary writes
MIN_SYNOPSIS_LEN = 5
HOME_URL = "https://www.egyptiantheatre.com/"
TITLES_URL = f"{HOME_URL}special-engagements"

IMAGE_URL_PREFIX = "https://cms.ntflxthtrs.com/"
DETAIL_URL_PREFIX = f"{HOME_URL}film/"

def fetch_document(url):
    with urlopen(url) as f:
        return f.read().decode('utf-8')

def extract_metadata(content):
    map = {}
    for tag_match in re.finditer(r'<meta( \w+="[^"]*")+/>', content):
        prop = None
        value = None
        for attr_match in re.finditer(r' (\w+)="([^"]*)"', tag_match.group(0)):
            if attr_match.group(1) == 'property' or attr_match.group(1) == 'name':
                prop = attr_match.group(2)
            if attr_match.group(1) == 'content':
                value = attr_match.group(2)
        if prop and value:
            map[prop] = value

    return map

def extract_json_blob(content):
    rx = r'<script>self\.__next_f\.push\(\[1,"b:(.*?)"\]\)</script>'
    items = [x.group(1) for x in re.finditer(rx, content)]

    if len(items) > 1:
        raise ValueError("Too many items")

    unescaped = items[0].encode('utf-8').decode('unicode_escape')
    reencoded = unescaped.encode('latin-1').decode('utf-8')

    return reencoded

def extract_titles(json_blob):
    dict = loads(json_blob)
    data = dict[-1]["children"][-1]["children"][-1][-1]["value"]["filmData"]["data"]
    return [x["attributes"] for x in data]

def extract_poster(title_blob):
    formats_blob = title_blob["Poster"]["data"]["attributes"]["formats"]
    for format in [ "medium", "small", "thumbnail" ]:
        if format in formats_blob:
            return urljoin(IMAGE_URL_PREFIX, formats_blob[format]["url"])
    return ""

def extract_detail_url(title_blob):
    return urljoin(DETAIL_URL_PREFIX, title_blob["Slug"])

def extract_cast(title_blob):
    return re.sub(r'\s+', " ", title_blob["Cast"] or "")

def extract_ymd(title_blob, key):
    return datetime.strptime(title_blob[key], '%Y-%m-%d')

def extract_updated(title_blob):
    updated_at = title_blob["updatedAt"]
    return isoparse(updated_at)

def extract_text(title_blob, key):
    return (title_blob[key] or "").strip()

def generate_html_body(title_blob):
    items = []
    if showtime := extract_text(title_blob, "RedLabelOverride"):
        items.append(f"""<p>{escape(showtime)}</p>""")
    if director := extract_text(title_blob, "Director"):
        items.append(f"""<p>Director: {escape(director)}</p>""")
    if cast := extract_cast(title_blob):
        items.append(f"""<p>Cast: {escape(cast)}</p>""")
    if synopsis := extract_text(title_blob, "Synopsis"):
        if len(synopsis.strip()) >= MIN_SYNOPSIS_LEN:
            items.append(f"""<p>{escape(synopsis.strip())}</p>""")
    if url := extract_poster(title_blob):
        items.append(f"""<img src="{url}" />""")

    return f"""<div>
{"\n".join(items)}
</div>"""

def _create_feed(url, metadata_map, ref_time) -> Feed:
    content = Feed()
    content.feed_url = url
    content.title = metadata_map["og:title"]
    content.description = metadata_map["og:description"]
    content.site_url = HOME_URL
    content.published = ref_time.timestamp()
    content.digest = content.computed_digest()

    return content

def _create_entry(title_blob) -> Entry:
    title = extract_text(title_blob, "FilmName")
    body = generate_html_body(title_blob)
    opening = extract_ymd(title_blob, "OpeningDate")
    closing = extract_ymd(title_blob, "ClosingDate")

    if opening != closing:
        time_range = f"{opening.strftime("%a %b %-d")} - {closing.strftime("%a %b %-d")}"
    else:
        time_range = opening.strftime("%a %b %-d")

    content = Entry()
    content.entry_uid = extract_text(title_blob, "Slug")
    content.title = f"""{title} ({time_range})"""
    content.author = extract_text(title_blob, "Director")
    content.link = extract_detail_url(title_blob)
    content.text_body = sanitizer.sanitize_html(body)
    content.published = extract_updated(title_blob).timestamp()
    synopsis = extract_text(title_blob, "Synopsis")
    if len(synopsis.strip()) >= MIN_SYNOPSIS_LEN:
        content.text_summary = sanitizer.extract_text(synopsis, max_len=consts.MAX_SUMMARY_LEN)
    else:
        content.text_summary = ""
    content.digest = content.computed_digest()

    return content

def matcher(url):
    return url.startswith(HOME_URL)

def parser(url):
    if not matcher(url):
        raise ValueError("URL not matching pattern")

    return parse(url, TITLES_URL, datetime.now())

def parse(request_url, feed_url, ref_time):
    document = fetch_document(feed_url)
    md_map = extract_metadata(document)
    json_content = extract_json_blob(document)
    titles = extract_titles(json_content)

    return ParseResult(
        request_url,
        feed=_create_feed(request_url, md_map, ref_time),
        entries=[_create_entry(title) for title in titles],
    )
