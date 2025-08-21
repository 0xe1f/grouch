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
from parser.custom import amecine
from zoneinfo import ZoneInfo
import json
import pathlib
import unittest

class TestAmericanCinemathequeParser(unittest.TestCase):

    FEED_URL = "https://www.americancinematheque.com/now-showing/"
    SOURCE_JSON_PATH = "tests/resources/amecine_s.json"
    VERIFY_JSON_PATH = "tests/resources/amecine_v.json"
    REF_TIME = datetime(2025, 8, 18, 22, 32, 11, 0, tzinfo=ZoneInfo(key='America/Los_Angeles'))

    def test_amecine_parsing_feed(self):
        request_uri = self.__class__.FEED_URL
        feed_path = abspath(self.__class__.SOURCE_JSON_PATH)
        feed_uri = pathlib.Path(feed_path).as_uri()
        ref_time = self.__class__.REF_TIME
        result = amecine.parse(request_uri, feed_uri, ref_time)

        parsed = {
            'feed': result.feed._doc,
            'entries': [x._doc for x in result.entries],
        }
        with open(self.__class__.VERIFY_JSON_PATH) as file:
            verification = json.load(file)

        self.assertEqual(request_uri, result.url, "url")
        self.assertEqual(verification['feed'], parsed['feed'], "feed content")
        self.assertEqual(verification['entries'], parsed['entries'], "list of entries")

    def test_amecine_url_matching(self):
        prefix = self.__class__.FEED_URL
        self.assertTrue(amecine.matcher(f'{prefix}'))
        self.assertTrue(amecine.matcher(f'{prefix}abcdef'))
        self.assertTrue(amecine.matcher(f'{prefix}abc/def#123'))
        self.assertFalse(amecine.matcher('https://www.random.org/'))
