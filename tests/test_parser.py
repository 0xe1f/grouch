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

from parser import parse_url
import json
import unittest

class TestAtomParsing(unittest.TestCase):

    XML_PATH = "tests/resources/feed_atom.xml"
    JSON_PATH = "tests/resources/feed_atom.json"
    ENTRY_COUNT = 25

    def test_atom_parsing_feed(self):
        feed_url = __class__.XML_PATH
        result = parse_url(feed_url)

        self.assertIsNotNone(result)
        self.assertIsNotNone(feed := result.feed)

        # Load proto - we'll use this to verify content obtained
        # from parser
        with open(__class__.JSON_PATH) as file:
            proto = json.load(file)
        feed_proto = proto["feed"]

        # Verify items
        self.assertEqual(feed_url, feed.feed_url)
        for k, v in feed_proto.items():
            self.assertEqual(v, getattr(feed, k))

        # Verify digest
        self.assertTrue(feed.digest)
        self.assertEqual(feed.digest, feed.computed_digest())

    def test_atom_parsing_entries(self):
        feed_url = __class__.XML_PATH
        result = parse_url(feed_url)

        self.assertIsNotNone(result)
        self.assertIsNotNone(entries := result.entries)

        # Load proto - we'll use this to verify content obtained
        # from parser
        with open(__class__.JSON_PATH) as file:
            proto = json.load(file)
        entries_proto = proto["entries"]

        # Verify total count
        self.assertEqual(__class__.ENTRY_COUNT, len(entries))

        # Verify each item
        for ix, entry in enumerate(entries):
            entry_proto = entries_proto[ix]
            for k, v in entry_proto.items():
                self.assertEqual(v, getattr(entry, k), f"Check failed, entry index #{ix}")

            self.assertTrue(entry.digest)
            self.assertEqual(entry.digest, entry.computed_digest())

class TestRss1Parsing(unittest.TestCase):

    XML_PATH = "tests/resources/feed_rss1.xml"
    JSON_PATH = "tests/resources/feed_rss1.json"
    ENTRY_COUNT = 15

    def test_rss1_parsing_feed(self):
        feed_url = __class__.XML_PATH
        result = parse_url(feed_url)

        self.assertIsNotNone(result)
        self.assertIsNotNone(feed := result.feed)

        # Load proto - we'll use this to verify content obtained
        # from parser
        with open(__class__.JSON_PATH) as file:
            proto = json.load(file)
        feed_proto = proto["feed"]

        # Verify items
        self.assertEqual(feed_url, feed.feed_url)
        for k, v in feed_proto.items():
            self.assertEqual(v, getattr(feed, k))

        # Verify digest
        self.assertTrue(feed.digest)
        self.assertEqual(feed.digest, feed.computed_digest())

    def test_rss1_parsing_entries(self):
        feed_url = __class__.XML_PATH
        result = parse_url(feed_url)

        self.assertIsNotNone(result)
        self.assertIsNotNone(entries := result.entries)

        # Load proto - we'll use this to verify content obtained
        # from parser
        with open(__class__.JSON_PATH) as file:
            proto = json.load(file)
        entries_proto = proto["entries"]

        # Verify total count
        self.assertEqual(__class__.ENTRY_COUNT, len(entries))

        # Verify each item
        for ix, entry in enumerate(entries):
            entry_proto = entries_proto[ix]
            for k, v in entry_proto.items():
                self.assertEqual(v, getattr(entry, k), f"Check failed, entry index #{ix}")

            self.assertTrue(entry.digest)
            self.assertEqual(entry.digest, entry.computed_digest())

class TestRss2Parsing(unittest.TestCase):

    XML_PATH = "tests/resources/feed_rss2.xml"
    JSON_PATH = "tests/resources/feed_rss2.json"
    ENTRY_COUNT = 20

    def test_rss2_parsing_feed(self):
        feed_url = __class__.XML_PATH
        result = parse_url(feed_url)

        self.assertIsNotNone(result)
        self.assertIsNotNone(feed := result.feed)

        # Load proto - we'll use this to verify content obtained
        # from parser
        with open(__class__.JSON_PATH) as file:
            proto = json.load(file)
        feed_proto = proto["feed"]

        # Verify items
        self.assertEqual(feed_url, feed.feed_url)
        for k, v in feed_proto.items():
            self.assertEqual(v, getattr(feed, k))

        # Verify digest
        self.assertTrue(feed.digest)
        self.assertEqual(feed.digest, feed.computed_digest())

    def test_rss2_parsing_entries(self):
        feed_url = __class__.XML_PATH
        result = parse_url(feed_url)

        self.assertIsNotNone(result)
        self.assertIsNotNone(entries := result.entries)

        # Load proto - we'll use this to verify content obtained
        # from parser
        with open(__class__.JSON_PATH) as file:
            proto = json.load(file)
        entries_proto = proto["entries"]

        # Verify total count
        self.assertEqual(__class__.ENTRY_COUNT, len(entries))

        # Verify each item
        for ix, entry in enumerate(entries):
            entry_proto = entries_proto[ix]
            for k, v in entry_proto.items():
                self.assertEqual(v, getattr(entry, k), f"Check failed, entry index #{ix}")

            self.assertTrue(entry.digest)
            self.assertEqual(entry.digest, entry.computed_digest())

if __name__ == '__main__':
    unittest.main()
