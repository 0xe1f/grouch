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

from datatype.folder import Folder
from datatype.feed_content import FeedContent
from datatype.subscription import Subscription
from port.objects import PortDoc
from port.objects import Group
from port.objects import Source
from port.opml import write_opml
from port.opml import read_opml

SubMeta = tuple[Subscription, FeedContent]

def export_opml(title: str, subs: list[SubMeta], folders: list[Folder]) -> str:
    doc = _to_doc(subs, folders)
    return write_opml(doc, title)

def import_opml(fp) -> PortDoc:
    return read_opml(fp)

def _to_doc(subs: list[SubMeta], folders: list[Folder]) -> PortDoc:
    doc = PortDoc()
    for folder in folders:
        group = Group(folder.id, folder.title)
        doc.append_group(group)

    for sub, feed in subs:
        source = Source(sub.title, feed.feed_url, sub.folder_id)
        source.html_url = feed.site_url
        doc.append_source(source)

    return doc
