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
import hashlib
import json
import unittest
import uuid

FLEX_DICT = {
    "id": uuid.uuid4().hex,
    "rev": uuid.uuid4().hex,
    "doc_type": uuid.uuid4().hex,
    "updated": uuid.uuid4().hex,
}

class TestFeedContent(unittest.TestCase):

    DIGEST_DICT = {
        "feed_url": uuid.uuid4().hex,
        "title": uuid.uuid4().hex,
        "description": uuid.uuid4().hex,
        "favicon_url": uuid.uuid4().hex,
        "site_url": uuid.uuid4().hex,
        "published": uuid.uuid4().hex,
    }   

    def test_feed_properties(self):
        obj = Feed()
        self.assertEqual(Feed.DOC_TYPE, obj.doc_type)

        for k, v in __class__.DIGEST_DICT.items():
            self.assertTrue(hasattr(obj, k))
            setattr(obj, k, v)
            self.assertEqual(getattr(obj, k), v)
        for k, v in FLEX_DICT.items():
            self.assertTrue(hasattr(obj, k))
            setattr(obj, k, v)
            self.assertEqual(getattr(obj, k), v)

    def test_feed_digest_computation(self):
        obj = Feed()
        for k, v in __class__.DIGEST_DICT.items():
            setattr(obj, k, v)

        m = hashlib.md5()
        m.update(json.dumps(self.__class__.DIGEST_DICT).encode())
        computed_digest = m.hexdigest()

        self.assertEqual(computed_digest, obj.computed_digest())

    def test_feed_digest_recomputed(self):
        obj = Feed()
        previous_digest = obj.computed_digest()
        for k, v in __class__.DIGEST_DICT.items():
            setattr(obj, k, v)
            digest = obj.computed_digest()
            self.assertTrue(digest)
            self.assertNotEqual(previous_digest, digest)
            previous_digest = digest

    def test_feed_digest_unchaged(self):
        obj = Feed()

        previous_digest = obj.computed_digest()
        for k, v in FLEX_DICT.items():
            setattr(obj, k, v)
            digest = obj.computed_digest()
            self.assertTrue(digest)
            self.assertEqual(previous_digest, digest)
            previous_digest = digest

class TestEntryContent(unittest.TestCase):

    DIGEST_DICT = {
        "entry_uid": uuid.uuid4().hex,
        "title": uuid.uuid4().hex,
        "author": uuid.uuid4().hex,
        "link": uuid.uuid4().hex,
        "text_body": uuid.uuid4().hex,
        "text_summary": uuid.uuid4().hex,
        "published": uuid.uuid4().hex,
    }   

    def test_entry_properties(self):
        obj = Entry()
        self.assertEqual(Entry.DOC_TYPE, obj.doc_type)

        for k, v in __class__.DIGEST_DICT.items():
            self.assertTrue(hasattr(obj, k))
            setattr(obj, k, v)
            self.assertEqual(getattr(obj, k), v)
        for k, v in FLEX_DICT.items():
            self.assertTrue(hasattr(obj, k))
            setattr(obj, k, v)
            self.assertEqual(getattr(obj, k), v)

    def test_entry_digest_computation(self):
        obj = Entry()
        for k, v in __class__.DIGEST_DICT.items():
            setattr(obj, k, v)

        m = hashlib.md5()
        m.update(json.dumps(self.__class__.DIGEST_DICT).encode())
        computed_digest = m.hexdigest()

        self.assertEqual(computed_digest, obj.computed_digest())

    def test_entry_digest_recomputed(self):
        obj = Entry()
        previous_digest = obj.computed_digest()
        for k, v in __class__.DIGEST_DICT.items():
            setattr(obj, k, v)
            digest = obj.computed_digest()
            self.assertTrue(digest)
            self.assertNotEqual(previous_digest, digest)
            previous_digest = digest

    def test_entry_digest_unchaged(self):
        obj = Entry()

        previous_digest = obj.computed_digest()
        for k, v in FLEX_DICT.items():
            setattr(obj, k, v)
            digest = obj.computed_digest()
            self.assertTrue(digest)
            self.assertEqual(previous_digest, digest)
            previous_digest = digest

if __name__ == '__main__':
    unittest.main()
