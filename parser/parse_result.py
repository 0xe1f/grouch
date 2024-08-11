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

from datatype import EntryContent
from datatype import FeedContent

class ParseResult:

    def __init__(self, url: str, error: str=None, feed: FeedContent=None, entries: list[EntryContent]=None):
        self._url = url
        self._feed = feed
        self._entries = entries
        self._error = error

    @property
    def url(self) -> str:
        return self._url

    @property
    def feed(self) -> FeedContent|None:
        return self._feed

    @property
    def entries(self) -> list[EntryContent]|None:
        return self._entries

    @property
    def error(self) -> str|None:
        return self._error

    def success(self) -> bool:
        return not self.error
