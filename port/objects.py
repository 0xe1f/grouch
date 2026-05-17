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

class Base:

    def __init__(self, title: str|None=None):
        self._title = title

    @property
    def title(self) -> str:
        return self._title

class Group(Base):

    def __init__(self, id: str|None=None, title: str|None=None):
        super().__init__(title)
        self._id = id

    @property
    def id(self) -> str:
        return self._id

    def to_dict(self) -> dict:
        return {
            'id': self._id,
            'title': self._title,
        }

    @classmethod
    def from_dict(cls, d: dict) -> 'Group':
        return cls(id=d.get('id'), title=d.get('title'))

class Source(Base):

    def __init__(self, title: str|None=None, feed_url: str|None=None, parent_id: str|None=None):
        super().__init__(title)
        self._feed_url = feed_url
        self._parent_id = parent_id
        self._html_url = None

    @property
    def feed_url(self) -> str:
        return self._feed_url

    @property
    def parent_id(self) -> str:
        return self._parent_id

    @property
    def html_url(self) -> str:
        return self._html_url

    @html_url.setter
    def html_url(self, val: str):
        self._html_url = val

    def to_dict(self) -> dict:
        return {
            'title': self._title,
            'feed_url': self._feed_url,
            'parent_id': self._parent_id,
            'html_url': self._html_url,
        }

    @classmethod
    def from_dict(cls, d: dict) -> 'Source':
        s = cls(
            title=d.get('title'),
            feed_url=d.get('feed_url'),
            parent_id=d.get('parent_id'),
        )
        s._html_url = d.get('html_url')
        return s

class PortDoc:

    def __init__(self):
        self._groups = []
        self._sources = []
        self._group_map = {}
        self._source_map = {}

    @property
    def groups(self) -> list[Group]:
        return self._groups

    @property
    def sources(self) -> list[Source]:
        return self._sources

    def find_group(self, group_id: str) -> Group|None:
        return self._group_map.get(group_id)

    def find_sources(self, parent_id: str|None=None) -> list[Source]|None:
        return self._source_map.get(parent_id, [])

    def append_group(self, group: Group):
        self._groups.append(group)
        self._group_map[group.id] = group

    def append_source(self, source: Source):
        self._sources.append(source)
        # Sources with no parents are acceptable for map
        sources = self._source_map.setdefault(source.parent_id, [])
        sources.append(source)

    def to_dict(self) -> dict:
        return {
            'groups': [g.to_dict() for g in self._groups],
            'sources': [s.to_dict() for s in self._sources],
        }

    @classmethod
    def from_dict(cls, d: dict) -> 'PortDoc':
        doc = cls()
        for g in d.get('groups', []):
            doc.append_group(Group.from_dict(g))
        for s in d.get('sources', []):
            doc.append_source(Source.from_dict(s))
        return doc
