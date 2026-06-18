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
from parser import parse_feed
from parser import parse
import functools
import http.server
import json
import socketserver
import threading
import unittest

_RESOURCES_DIR = "tests/resources"

# parse_url now fetches over HTTP (with a timeout) instead of reading local
# paths, so the fixtures are served from a throwaway local HTTP server for the
# duration of the test module.
_server = None
_base_url = None

class _QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass

def setUpModule():
    global _server, _base_url
    handler = functools.partial(_QuietHandler, directory=_RESOURCES_DIR)
    _server = socketserver.ThreadingTCPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=_server.serve_forever, daemon=True).start()
    _base_url = f"http://127.0.0.1:{_server.server_address[1]}"

def tearDownModule():
    _server.shutdown()
    _server.server_close()

def _feed_url(filename: str) -> str:
    return f"{_base_url}/{filename}"

class TestAtomParsing(unittest.TestCase):

    XML_FILE = "feed_atom.xml"
    JSON_PATH = "tests/resources/feed_atom.json"
    ENTRY_COUNT = 25

    def test_atom_parsing_feed(self):
        feed_url = _feed_url(self.__class__.XML_FILE)
        result = parse_url(feed_url)

        self.assertIsNotNone(result)
        self.assertIsNotNone(feed := result.feed)

        # Load proto - we'll use this to verify content obtained
        # from parser
        with open(self.__class__.JSON_PATH) as file:
            proto = json.load(file)
        feed_proto = proto["feed"]
        # Fixtures are now served over HTTP, so the recorded feed_url no longer
        # matches; it is asserted separately just below.
        feed_proto["feed_url"] = feed_url

        # Verify items
        self.assertEqual(feed_url, feed.feed_url)
        for k, v in feed_proto.items():
            self.assertEqual(v, getattr(feed, k))

        # Verify digest
        self.assertTrue(feed.digest)
        self.assertEqual(feed.digest, feed.computed_digest())

    def test_atom_parsing_entries(self):
        feed_url = _feed_url(self.__class__.XML_FILE)
        result = parse_url(feed_url)

        self.assertIsNotNone(result)
        self.assertIsNotNone(entries := result.entries)

        # Load proto - we'll use this to verify content obtained
        # from parser
        with open(self.__class__.JSON_PATH) as file:
            proto = json.load(file)
        entries_proto = proto["entries"]

        # Verify total count
        self.assertEqual(self.__class__.ENTRY_COUNT, len(entries))

        # Verify each item
        for ix, entry in enumerate(entries):
            entry_proto = entries_proto[ix]
            for k, v in entry_proto.items():
                self.assertEqual(v, getattr(entry, k), f'Check failed, entry (index:{ix},key:{k})')

            self.assertTrue(entry.digest)
            self.assertEqual(entry.digest, entry.computed_digest())

class TestRss1Parsing(unittest.TestCase):

    XML_FILE = "feed_rss1.xml"
    JSON_PATH = "tests/resources/feed_rss1.json"
    ENTRY_COUNT = 15

    def test_rss1_parsing_feed(self):
        feed_url = _feed_url(self.__class__.XML_FILE)
        result = parse_url(feed_url)

        self.assertIsNotNone(result)
        self.assertIsNotNone(feed := result.feed)

        # Load proto - we'll use this to verify content obtained
        # from parser
        with open(self.__class__.JSON_PATH) as file:
            proto = json.load(file)
        feed_proto = proto["feed"]
        # Fixtures are now served over HTTP, so the recorded feed_url no longer
        # matches; it is asserted separately just below.
        feed_proto["feed_url"] = feed_url

        # Verify items
        self.assertEqual(feed_url, feed.feed_url)
        for k, v in feed_proto.items():
            self.assertEqual(v, getattr(feed, k))

        # Verify digest
        self.assertTrue(feed.digest)
        self.assertEqual(feed.digest, feed.computed_digest())

    def test_rss1_parsing_entries(self):
        feed_url = _feed_url(self.__class__.XML_FILE)
        result = parse_url(feed_url)

        self.assertIsNotNone(result)
        self.assertIsNotNone(entries := result.entries)

        # Load proto - we'll use this to verify content obtained
        # from parser
        with open(self.__class__.JSON_PATH) as file:
            proto = json.load(file)
        entries_proto = proto["entries"]

        # Verify total count
        self.assertEqual(self.__class__.ENTRY_COUNT, len(entries))

        # Verify each item
        for ix, entry in enumerate(entries):
            entry_proto = entries_proto[ix]
            for k, v in entry_proto.items():
                self.assertEqual(v, getattr(entry, k), f"Check failed, entry (index:{ix},key:{k})")

            self.assertTrue(entry.digest)
            self.assertEqual(entry.digest, entry.computed_digest())

class TestRss2Parsing(unittest.TestCase):

    XML_FILE = "feed_rss2.xml"
    JSON_PATH = "tests/resources/feed_rss2.json"
    ENTRY_COUNT = 20

    def test_rss2_parsing_feed(self):
        feed_url = _feed_url(self.__class__.XML_FILE)
        result = parse_url(feed_url)

        self.assertIsNotNone(result)
        self.assertIsNotNone(feed := result.feed)

        # Load proto - we'll use this to verify content obtained
        # from parser
        with open(self.__class__.JSON_PATH) as file:
            proto = json.load(file)
        feed_proto = proto["feed"]
        # Fixtures are now served over HTTP, so the recorded feed_url no longer
        # matches; it is asserted separately just below.
        feed_proto["feed_url"] = feed_url

        # Verify items
        self.assertEqual(feed_url, feed.feed_url)
        for k, v in feed_proto.items():
            self.assertEqual(v, getattr(feed, k))

        # Verify digest
        self.assertTrue(feed.digest)
        self.assertEqual(feed.digest, feed.computed_digest())

    def test_rss2_parsing_entries(self):
        feed_url = _feed_url(self.__class__.XML_FILE)
        result = parse_url(feed_url)

        self.assertIsNotNone(result)
        self.assertIsNotNone(entries := result.entries)

        # Load proto - we'll use this to verify content obtained
        # from parser
        with open(self.__class__.JSON_PATH) as file:
            proto = json.load(file)
        entries_proto = proto["entries"]

        # Verify total count
        self.assertEqual(self.__class__.ENTRY_COUNT, len(entries))

        # Verify each item
        for ix, entry in enumerate(entries):
            entry_proto = entries_proto[ix]
            for k, v in entry_proto.items():
                self.assertEqual(v, getattr(entry, k), f"Check failed, entry (index:{ix},key:{k})")

            self.assertTrue(entry.digest, f"Check failed, entry index #{ix}")
            self.assertEqual(entry.digest, entry.computed_digest(), f"Check failed, entry index #{ix}")


_FEED_ETAG = '"v1-etag"'
_FEED_LAST_MODIFIED = "Wed, 17 Jun 2026 00:00:00 GMT"

class _ConditionalHandler(http.server.BaseHTTPRequestHandler):
    """Serves a feed with an ETag/Last-Modified and honors If-None-Match."""

    feed_bytes = b""

    def do_GET(self):
        if self.headers.get("If-None-Match") == _FEED_ETAG:
            self.send_response(304)
            self.send_header("ETag", _FEED_ETAG)
            self.end_headers()
            return
        self.send_response(200)
        self.send_header("Content-Type", "application/rss+xml; charset=utf-8")
        self.send_header("ETag", _FEED_ETAG)
        self.send_header("Last-Modified", _FEED_LAST_MODIFIED)
        self.send_header("Content-Length", str(len(self.feed_bytes)))
        self.end_headers()
        self.wfile.write(self.feed_bytes)

    def log_message(self, *args):
        pass

class TestConditionalGet(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        with open("tests/resources/feed_rss2.xml", "rb") as f:
            _ConditionalHandler.feed_bytes = f.read()
        cls._server = socketserver.ThreadingTCPServer(("127.0.0.1", 0), _ConditionalHandler)
        threading.Thread(target=cls._server.serve_forever, daemon=True).start()
        cls._url = f"http://127.0.0.1:{cls._server.server_address[1]}/feed"

    @classmethod
    def tearDownClass(cls):
        cls._server.shutdown()
        cls._server.server_close()

    def test_fetch_captures_validators(self):
        fetched = parse._fetch_url(self.__class__._url)
        self.assertIsNotNone(fetched)
        self.assertFalse(fetched.not_modified)
        self.assertTrue(fetched.content)
        self.assertEqual(_FEED_ETAG, fetched.etag)
        self.assertEqual(_FEED_LAST_MODIFIED, fetched.last_modified)

    def test_fetch_304_when_etag_matches(self):
        fetched = parse._fetch_url(self.__class__._url, etag=_FEED_ETAG)
        self.assertIsNotNone(fetched)
        self.assertTrue(fetched.not_modified)
        self.assertIsNone(fetched.content)

    def test_parse_feed_sets_validators_on_feed(self):
        result = parse_feed(self.__class__._url)
        self.assertFalse(result.not_modified)
        self.assertIsNotNone(result.feed)
        self.assertEqual(_FEED_ETAG, result.feed.etag)
        self.assertEqual(_FEED_LAST_MODIFIED, result.feed.last_modified)

    def test_parse_feed_not_modified_skips_parsing(self):
        result = parse_feed(self.__class__._url, etag=_FEED_ETAG)
        self.assertTrue(result.not_modified)
        self.assertIsNone(result.feed)
        self.assertIsNone(result.entries)

    def test_parse_feed_stale_etag_returns_content(self):
        result = parse_feed(self.__class__._url, etag='"stale"')
        self.assertFalse(result.not_modified)
        self.assertIsNotNone(result.feed)
        self.assertTrue(result.entries)
