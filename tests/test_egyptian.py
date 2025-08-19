# Copyright (C) 2025 Akop Karapetyan
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

from datetime import datetime
from os.path import abspath
from parser.custom import egyptian
import json
import pathlib
import unittest

class TestEgyptianParser(unittest.TestCase):

    FEED_URL = "https://www.egyptiantheatre.com/"
    HTML_PATH = "tests/resources/egyptian.html"
    JSON_PATH = "tests/resources/egyptian.json"
    REF_TIME = datetime(2025, 8, 18, 22, 32, 11)

    def test_egyptian_parsing_feed(self):
        request_uri = self.__class__.FEED_URL
        feed_path = abspath(self.__class__.HTML_PATH)
        feed_uri = pathlib.Path(feed_path).as_uri()
        ref_time = self.__class__.REF_TIME
        result = egyptian.parse(request_uri, feed_uri, ref_time)

        parsed = {
            'feed': result.feed._doc,
            'entries': [x._doc for x in result.entries],
        }
        with open(self.__class__.JSON_PATH) as file:
            verification = json.load(file)

        self.assertEqual(request_uri, result.url, "url")
        self.assertEqual(verification['feed'], parsed['feed'], "feed content")
        self.assertEqual(verification['entries'], parsed['entries'], "list of entries")

    def test_egyptian_url_matching(self):
        prefix = self.__class__.FEED_URL
        self.assertTrue(egyptian.matcher(f'{prefix}'))
        self.assertTrue(egyptian.matcher(f'{prefix}abcdef'))
        self.assertTrue(egyptian.matcher(f'{prefix}abc/def#123'))
        self.assertFalse(egyptian.matcher('https://www.random.org/'))
