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
from datetime import timedelta
from html import escape
from json import loads
from urllib.request import urlopen
import pytz

home_url = "https://www.americancinematheque.com/now-showing/"
feed_url_template = "https://www.americancinematheque.com/wp-json/wp/v2/algolia_get_events?environment=production&startDate={0}&endDate={1}"
tz = pytz.timezone('US/Pacific')

def fetch_document(url):
    with urlopen(url) as f:
        return f.read().decode('utf-8')

def extract_text(blob, key):
    return (blob[key] or "").strip()

def extract_date_time(blob, date_key, time_key):
    return datetime.strptime(f"{blob[date_key]} {blob[time_key]}", '%Y%m%d %H:%M:%S').replace(tzinfo=tz)

def extract_opening_date_time(blob):
    return extract_date_time(blob, "event_start_date", "event_start_time")

def extract_closing_date_time(blob):
    return extract_date_time(blob, "event_end_date", "event_end_time")

def generate_title(blob):
    start_date = extract_opening_date_time(blob)
    return f"""{extract_text(blob, 'title')} ({start_date.strftime("%a %b %-d")})"""

def generate_html_body(blob):
    items = []
    if start_date_time := extract_opening_date_time(blob):
        items.append(f"""<p>{start_date_time.strftime("%a %b %d | %H:%M")}</p>""")
    if synopsis := extract_text(blob, "event_card_excerpt"):
        items.append(f"""<p>{escape(sanitizer.extract_text(synopsis))}</p>""")
    if url := blob["event_card_image"]["url"]:
        items.append(f"""<img src="{url}" />""")

    return f"""<div>
{"\n".join(items)}
</div>"""

def _create_feed(url, ref_time) -> Feed:
    content = Feed()
    content.feed_url = url
    content.title = "Now Showing - American Cinematheque"
    content.description = ""
    content.site_url = home_url
    content.published = ref_time.timestamp()
    content.digest = content.computed_digest()

    return content

def _create_entry(blob, ref_time) -> Entry:
    body = generate_html_body(blob)
    synopsis = extract_text(blob, "event_card_excerpt")

    content = Entry()
    content.entry_uid = blob['objectID']
    content.title = generate_title(blob)
    # content.author = ?
    content.link = extract_text(blob, 'url')
    content.text_body = sanitizer.sanitize_html(body)
    content.published = ref_time.timestamp()
    content.text_summary = sanitizer.extract_text(synopsis, max_len=consts.MAX_SUMMARY_LEN)
    content.digest = content.computed_digest()

    return content

def matcher(url):
    return url.startswith(home_url)

def parser(url):
    if not matcher(url):
        raise ValueError("URL not matching pattern")

    start_dt = datetime.combine(datetime.today(), datetime.min.time())
    end_dt = start_dt + timedelta(days=30)
    feed_url = feed_url_template.format(int(start_dt.timestamp()), int(end_dt.timestamp()))

    return parse(url, feed_url, datetime.now())

def parse(request_url, feed_url, ref_time):
    document = loads(fetch_document(feed_url))
    return ParseResult(
        request_url,
        feed=_create_feed(request_url, ref_time),
        entries=[_create_entry(title, ref_time) for title in document['hits'] if title['post_type'] == 'event'],
    )
