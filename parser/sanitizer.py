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

from lxml.html import clean
import html

_SANITIZER = clean.Cleaner(
    allow_tags=[
        "a",
        "address",
        "em",
        "strong",
        "b",
        "i",
        "big",
        "small",
        "sub",
        "sup",
        "cite",
        "code",
        "ol",
        "ul",
        "li",
        "dl",
        "lh",
        "dt",
        "dd",
        "p",
        "table",
        "tr",
        "th",
        "td",
        "pre",
        "blockquote",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "div",
        "span",
        "ins",
        "del",
        "img",
    ],
    safe_attrs_only=True,
)
_CLEANER = clean.Cleaner(
    allow_tags=[''],
)

def sanitize_html(content: str) -> str:
    return _SANITIZER.clean_html(content)

def extract_text(content: str, max_len: int=None) -> str:
    content = _CLEANER.clean_html(content)
    content = _strip_bookend_tags(content)

    if max_len and len(content) > max_len:
        content = content[:max_len]

    return html.unescape(content)

def _strip_bookend_tags(content: str) -> str:
    # Remove the div tags Cleaner inserts
    if content.startswith("<div>"):
        content = content[5:]
    if content.endswith("</div>"):
        content = content[:-6]

    return content
