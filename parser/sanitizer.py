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

from lxml_html_clean import Cleaner
from lxml.html import fromstring
import html
import re

_SANITIZER = Cleaner(
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
REGEX_WHITESPACE = r"\s+"

def sanitize_html(content: str) -> str:
    if not content:
        return content
    return _SANITIZER.clean_html(content)

def extract_text(content: str, max_len: int=None) -> str:
    if not content:
        return content

    text = fromstring(content).text_content()

    # Unescape HTML entities before truncating to avoid cutting mid-entity
    text = html.unescape(text)

    # Trim to necessary length.
    # This might result in shorter text than expected, but that's OK
    if max_len and len(text) > max_len:
        text = text[:max_len]

    return re.sub(REGEX_WHITESPACE, " ", text).strip()
