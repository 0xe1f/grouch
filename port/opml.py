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

from port.objects import Group
from port.objects import PortDoc
from port.objects import Source
from opml import OpmlDocument
from opml.outlinable import Outlinable
from uuid import uuid4

def write_opml(doc: PortDoc, title: str) -> str:
    opml = OpmlDocument()
    opml.title = title
    _write_outlinable(opml, doc.find_sources())
    for group in doc.groups:
        outline = opml.add_outline(
            text=group.title,
            title=group.title,
        )
        _write_outlinable(outline, doc.find_sources(group.id))

    return opml.dumps(pretty=True)

def read_opml(file) -> PortDoc:
    if opml := OpmlDocument.load(file):
        doc = PortDoc()
        _read_outlinable(opml, doc)
        return doc

    return None

def _write_outlinable(outline: Outlinable, sources: list[Source]):
    for source in sources:
        outline.add_rss(
            text=source.title,
            title=source.title,
            html_url=source.html_url,
            xml_url=source.feed_url
        )

def _read_outlinable(outlinable: Outlinable, doc: PortDoc, parent_id: str|None=None):
    for outline in outlinable.outlines:
        if not outline.xml_url:
            # Group
            group = Group(
                id=uuid4().hex,
                title=outline.title,
            )
            doc.append_group(group)
            _read_outlinable(outline, doc, group.id)
        elif outline.type == "rss":
            # Source
            source = Source(
                title=outline.title,
                feed_url=outline.xml_url,
                parent_id=parent_id,
            )
            doc.append_source(source)

    return doc
