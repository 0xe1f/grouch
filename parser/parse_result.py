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

from entity import Entry
from entity import Feed

class ParseResult:

    def __init__(self, url: str, feed: Feed|None=None, entries: list[Entry]|None=None, alts: list[str]|None=None):
        self._url = url
        self._feed = feed
        self._entries = entries
        self._alternatives = alts

    @property
    def url(self) -> str:
        return self._url

    @property
    def feed(self) -> Feed|None:
        return self._feed

    @property
    def entries(self) -> list[Entry]|None:
        return self._entries

    @property
    def alternatives(self) -> list[str]|None:
        return self._alternatives
