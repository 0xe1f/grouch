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

from io import BytesIO
from port.objects import Group
from port.objects import PortDoc
from port.objects import Source
from port.opml import read_opml
from port.opml import write_opml
import unittest


def _make_doc(*groups_and_sources) -> PortDoc:
    doc = PortDoc()
    for item in groups_and_sources:
        if isinstance(item, Group):
            doc.append_group(item)
        else:
            doc.append_source(item)
    return doc


class TestOpmlRoundtrip(unittest.TestCase):

    def test_roundtrip_grouped_sources(self):
        g1 = Group(id="g1", title="Tech")
        g2 = Group(id="g2", title="News")
        s1 = Source(title="Ars Technica", feed_url="https://arstechnica.com/feed", parent_id="g1")
        s2 = Source(title="Hacker News", feed_url="https://hnrss.org/frontpage", parent_id="g1")
        s3 = Source(title="BBC", feed_url="https://feeds.bbci.co.uk/news/rss.xml", parent_id="g2")

        doc = _make_doc(g1, g2, s1, s2, s3)
        opml_str = write_opml(doc, "My Subscriptions")
        result = read_opml(BytesIO(opml_str.encode()))

        self.assertIsNotNone(result)
        group_titles = {g.title for g in result.groups}
        self.assertEqual({"Tech", "News"}, group_titles)

        all_feed_urls = {s.feed_url for s in result.sources}
        self.assertIn("https://arstechnica.com/feed", all_feed_urls)
        self.assertIn("https://hnrss.org/frontpage", all_feed_urls)
        self.assertIn("https://feeds.bbci.co.uk/news/rss.xml", all_feed_urls)

    def test_roundtrip_ungrouped_sources(self):
        s1 = Source(title="Feed A", feed_url="https://example.com/a", parent_id=None)
        s2 = Source(title="Feed B", feed_url="https://example.com/b", parent_id=None)

        doc = _make_doc(s1, s2)
        opml_str = write_opml(doc, "Ungrouped")
        result = read_opml(BytesIO(opml_str.encode()))

        self.assertIsNotNone(result)
        self.assertEqual(0, len(result.groups))
        feed_urls = {s.feed_url for s in result.sources}
        self.assertEqual({"https://example.com/a", "https://example.com/b"}, feed_urls)

    def test_roundtrip_group_membership(self):
        g1 = Group(id="g1", title="Sports")
        s_grouped = Source(title="ESPN", feed_url="https://espn.com/rss", parent_id="g1")
        s_ungrouped = Source(title="Other", feed_url="https://other.com/rss", parent_id=None)

        doc = _make_doc(g1, s_grouped, s_ungrouped)
        opml_str = write_opml(doc, "Mixed")
        result = read_opml(BytesIO(opml_str.encode()))

        self.assertIsNotNone(result)
        self.assertEqual(1, len(result.groups))
        sports_group = result.groups[0]
        self.assertEqual("Sports", sports_group.title)

        grouped_sources = result.find_sources(sports_group.id)
        self.assertEqual(1, len(grouped_sources))
        self.assertEqual("https://espn.com/rss", grouped_sources[0].feed_url)

        ungrouped_sources = result.find_sources(None)
        self.assertEqual(1, len(ungrouped_sources))
        self.assertEqual("https://other.com/rss", ungrouped_sources[0].feed_url)

    def test_source_titles_preserved(self):
        s = Source(title="My Favorite Feed", feed_url="https://example.com/feed", parent_id=None)
        doc = _make_doc(s)
        opml_str = write_opml(doc, "Test")
        result = read_opml(BytesIO(opml_str.encode()))

        self.assertEqual("My Favorite Feed", result.sources[0].title)


class TestReadOpml(unittest.TestCase):

    def test_minimal_opml_no_groups(self):
        opml_bytes = b"""<?xml version="1.0" encoding="UTF-8"?>
<opml version="2.0">
  <head><title>Test</title></head>
  <body>
    <outline type="rss" text="Feed One" title="Feed One" xmlUrl="https://one.com/rss"/>
    <outline type="rss" text="Feed Two" title="Feed Two" xmlUrl="https://two.com/rss"/>
  </body>
</opml>"""
        result = read_opml(BytesIO(opml_bytes))

        self.assertIsNotNone(result)
        self.assertEqual(0, len(result.groups))
        self.assertEqual(2, len(result.sources))
        feed_urls = {s.feed_url for s in result.sources}
        self.assertEqual({"https://one.com/rss", "https://two.com/rss"}, feed_urls)

    def test_non_rss_outlines_skipped(self):
        opml_bytes = b"""<?xml version="1.0" encoding="UTF-8"?>
<opml version="2.0">
  <head><title>Test</title></head>
  <body>
    <outline type="rss" text="Valid Feed" title="Valid Feed" xmlUrl="https://valid.com/rss"/>
    <outline text="Not a feed" title="Not a feed"/>
  </body>
</opml>"""
        result = read_opml(BytesIO(opml_bytes))

        self.assertIsNotNone(result)
        self.assertEqual(1, len(result.sources))
        self.assertEqual("https://valid.com/rss", result.sources[0].feed_url)
        self.assertEqual(1, len(result.groups))
