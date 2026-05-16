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

from entity import Article
from entity import Entry
from entity import Feed
from entity import Folder
from entity import Subscription
from entity import User
import bcrypt
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

        for k, v in self.__class__.DIGEST_DICT.items():
            self.assertTrue(hasattr(obj, k))
            setattr(obj, k, v)
            self.assertEqual(getattr(obj, k), v)
        for k, v in FLEX_DICT.items():
            self.assertTrue(hasattr(obj, k))
            setattr(obj, k, v)
            self.assertEqual(getattr(obj, k), v)

    def test_feed_digest_computation(self):
        obj = Feed()
        for k, v in self.__class__.DIGEST_DICT.items():
            setattr(obj, k, v)

        m = hashlib.md5()
        m.update(json.dumps(self.__class__.DIGEST_DICT).encode())
        computed_digest = m.hexdigest()

        self.assertEqual(computed_digest, obj.computed_digest())

    def test_feed_digest_recomputed(self):
        obj = Feed()
        previous_digest = obj.computed_digest()
        for k, v in self.__class__.DIGEST_DICT.items():
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
    }   

    def test_entry_properties(self):
        obj = Entry()
        self.assertEqual(Entry.DOC_TYPE, obj.doc_type)

        for k, v in self.__class__.DIGEST_DICT.items():
            self.assertTrue(hasattr(obj, k))
            setattr(obj, k, v)
            self.assertEqual(getattr(obj, k), v)
        for k, v in FLEX_DICT.items():
            self.assertTrue(hasattr(obj, k))
            setattr(obj, k, v)
            self.assertEqual(getattr(obj, k), v)

    def test_entry_digest_computation(self):
        obj = Entry()
        for k, v in self.__class__.DIGEST_DICT.items():
            setattr(obj, k, v)

        m = hashlib.md5()
        m.update(json.dumps(self.__class__.DIGEST_DICT).encode())
        computed_digest = m.hexdigest()

        self.assertEqual(computed_digest, obj.computed_digest())

    def test_entry_digest_recomputed(self):
        obj = Entry()
        previous_digest = obj.computed_digest()
        for k, v in self.__class__.DIGEST_DICT.items():
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


class TestArticleContent(unittest.TestCase):

    def test_article_properties(self):
        obj = Article()
        self.assertEqual(Article.DOC_TYPE, obj.doc_type)

        for k, v in [
            ("user_id", uuid.uuid4().hex),
            ("entry_id", uuid.uuid4().hex),
            ("folder_id", uuid.uuid4().hex),
            ("subscription_id", uuid.uuid4().hex),
            ("published", 1234567890),
            ("synced", 9876543210),
        ]:
            setattr(obj, k, v)
            self.assertEqual(v, getattr(obj, k))

    def test_article_defaults_tags_and_props(self):
        obj = Article()
        self.assertEqual([], obj.tags)
        self.assertEqual([], obj.props)

    def test_article_tags_roundtrip(self):
        obj = Article()
        obj.tags = ["news", "tech"]
        self.assertEqual(["news", "tech"], obj.tags)

    def test_toggle_prop_off_to_on(self):
        obj = Article()
        obj.toggle_prop(Article.PROP_UNREAD)
        self.assertIn(Article.PROP_UNREAD, obj.props)

    def test_toggle_prop_on_to_off(self):
        obj = Article()
        obj.props = [Article.PROP_UNREAD]
        obj.toggle_prop(Article.PROP_UNREAD)
        self.assertNotIn(Article.PROP_UNREAD, obj.props)

    def test_toggle_prop_explicit_set_true(self):
        obj = Article()
        obj.toggle_prop(Article.PROP_STARRED, is_set=True)
        self.assertIn(Article.PROP_STARRED, obj.props)
        obj.toggle_prop(Article.PROP_STARRED, is_set=True)
        self.assertEqual(1, obj.props.count(Article.PROP_STARRED))

    def test_toggle_prop_explicit_set_false(self):
        obj = Article()
        obj.props = [Article.PROP_LIKED]
        obj.toggle_prop(Article.PROP_LIKED, is_set=False)
        self.assertNotIn(Article.PROP_LIKED, obj.props)

    def test_new_key_raises_without_user_id(self):
        obj = Article()
        obj.entry_id = uuid.uuid4().hex
        with self.assertRaises(ValueError):
            obj.new_key()

    def test_new_key_raises_without_entry_id(self):
        obj = Article()
        obj.user_id = uuid.uuid4().hex
        with self.assertRaises(ValueError):
            obj.new_key()

    def test_extract_owner_id(self):
        obj = Article()
        user_uid = uuid.uuid4().hex
        obj.user_id = f"user::{user_uid}"
        obj.entry_id = f"entry::feed123::entry456"
        key = obj.new_key()
        owner_id = Article.extract_owner_id(key)
        self.assertIsNotNone(owner_id)
        self.assertTrue(owner_id.startswith("user::"))

    def test_extract_owner_id_wrong_doc_type(self):
        self.assertIsNone(Article.extract_owner_id("feed::abc::def"))


class TestUserContent(unittest.TestCase):

    def test_user_properties(self):
        obj = User()
        self.assertEqual(User.DOC_TYPE, obj.doc_type)

        for k, v in [
            ("username", "testuser"),
            ("email_address", "test@example.com"),
            ("last_sync", 1234567890),
            ("created", 9876543210),
        ]:
            setattr(obj, k, v)
            self.assertEqual(v, getattr(obj, k))

    def test_uid_auto_generated(self):
        obj = User()
        self.assertTrue(obj.uid)

    def test_new_key_prefixed(self):
        obj = User()
        self.assertTrue(obj.new_key().startswith("user::"))

    def test_set_hashed_password_not_plaintext(self):
        obj = User()
        salt = bcrypt.gensalt()
        obj.set_hashed_password("mysecret", salt)
        self.assertNotEqual("mysecret", obj.hashed_password)
        self.assertTrue(obj.hashed_password)

    def test_plaintext_matching_stored_correct(self):
        obj = User()
        salt = bcrypt.gensalt()
        obj.set_hashed_password("mysecret", salt)
        self.assertTrue(obj.plaintext_matching_stored("mysecret"))

    def test_plaintext_matching_stored_wrong(self):
        obj = User()
        salt = bcrypt.gensalt()
        obj.set_hashed_password("mysecret", salt)
        self.assertFalse(obj.plaintext_matching_stored("wrongpassword"))


class TestFolderContent(unittest.TestCase):

    def test_folder_properties(self):
        obj = Folder()
        self.assertEqual(Folder.DOC_TYPE, obj.doc_type)

        obj.title = "My Folder"
        self.assertEqual("My Folder", obj.title)

        obj.user_id = "user::abc"
        self.assertEqual("user::abc", obj.user_id)

    def test_uid_auto_generated(self):
        obj = Folder()
        self.assertTrue(obj.uid)

    def test_new_key_contains_user_id_and_uid(self):
        obj = Folder()
        obj.user_id = "user::abc"
        obj.uid = "xyz"
        key = obj.new_key()
        self.assertIn("abc", key)
        self.assertIn("xyz", key)

    def test_extract_owner_id(self):
        obj = Folder()
        obj.user_id = "user::abc"
        obj.uid = "xyz"
        key = obj.new_key()
        owner_id = Folder.extract_owner_id(key)
        self.assertIsNotNone(owner_id)
        self.assertTrue(owner_id.startswith("user::"))

    def test_extract_owner_id_wrong_doc_type(self):
        self.assertIsNone(Folder.extract_owner_id("user::abc"))


class TestSubscriptionContent(unittest.TestCase):

    def test_subscription_properties(self):
        obj = Subscription()
        self.assertEqual(Subscription.DOC_TYPE, obj.doc_type)

        for k, v in [
            ("title", "My Sub"),
            ("feed_id", "feed::abc"),
            ("folder_id", "folder::xyz"),
            ("user_id", "user::def"),
            ("subscribed", 1234567890),
            ("last_synced", 9876543210),
        ]:
            setattr(obj, k, v)
            self.assertEqual(v, getattr(obj, k))

    def test_new_key_raises_without_user_id(self):
        obj = Subscription()
        obj.feed_id = "feed::abc"
        with self.assertRaises(ValueError):
            obj.new_key()

    def test_new_key_raises_without_feed_id(self):
        obj = Subscription()
        obj.user_id = "user::abc"
        with self.assertRaises(ValueError):
            obj.new_key()

    def test_extract_owner_id(self):
        obj = Subscription()
        obj.user_id = "user::abc"
        obj.feed_id = "feed::def"
        key = obj.new_key()
        owner_id = Subscription.extract_owner_id(key)
        self.assertIsNotNone(owner_id)
        self.assertTrue(owner_id.startswith("user::"))

    def test_extract_owner_id_wrong_doc_type(self):
        self.assertIsNone(Subscription.extract_owner_id("feed::abc::def"))
