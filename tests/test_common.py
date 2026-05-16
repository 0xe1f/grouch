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

from common.lists import first_index
from common.lists import first_or_none
from common.secret import deobfuscate_json
from common.secret import obfuscate_json
import unittest


class TestObfuscateJson(unittest.TestCase):

    def test_roundtrip_dict(self):
        payload = {"key": "value", "number": 42}
        self.assertEqual(payload, deobfuscate_json(obfuscate_json(payload)))

    def test_roundtrip_list(self):
        payload = [1, "two", None, True]
        self.assertEqual(payload, deobfuscate_json(obfuscate_json(payload)))

    def test_roundtrip_string(self):
        self.assertEqual("hello", deobfuscate_json(obfuscate_json("hello")))

    def test_roundtrip_integer(self):
        self.assertEqual(123, deobfuscate_json(obfuscate_json(123)))

    def test_roundtrip_none(self):
        self.assertIsNone(deobfuscate_json(obfuscate_json(None)))

    def test_tampered_mac_returns_none(self):
        token = obfuscate_json({"a": 1})
        payload_b64, mac_b64 = token.split("#")
        # Flip the first character of the MAC
        flipped = chr(ord(mac_b64[0]) ^ 1) + mac_b64[1:]
        tampered = f"{payload_b64}#{flipped}"
        self.assertIsNone(deobfuscate_json(tampered))

    def test_no_separator_returns_none(self):
        self.assertIsNone(deobfuscate_json("noseparatorhere"))

    def test_multiple_separators_returns_none(self):
        self.assertIsNone(deobfuscate_json("a#b#c"))

    def test_empty_string_returns_none(self):
        self.assertIsNone(deobfuscate_json(""))


class TestFirstOrNone(unittest.TestCase):

    def test_returns_first_element(self):
        self.assertEqual(1, first_or_none([1, 2, 3]))

    def test_returns_none_for_empty_list(self):
        self.assertIsNone(first_or_none([]))

    def test_returns_none_element_when_first_is_none(self):
        self.assertIsNone(first_or_none([None, 1, 2]))

    def test_works_with_strings(self):
        self.assertEqual("a", first_or_none(["a", "b"]))

    def test_single_element(self):
        self.assertEqual(42, first_or_none([42]))


class TestFirstIndex(unittest.TestCase):

    def test_returns_correct_index(self):
        self.assertEqual(2, first_index([10, 20, 30, 40], 30))

    def test_returns_first_occurrence(self):
        self.assertEqual(1, first_index([0, 5, 5, 5], 5))

    def test_returns_minus_one_when_not_found(self):
        self.assertEqual(-1, first_index([1, 2, 3], 99))

    def test_returns_minus_one_for_empty_list(self):
        self.assertEqual(-1, first_index([], "x"))

    def test_returns_zero_for_first_element(self):
        self.assertEqual(0, first_index(["a", "b", "c"], "a"))
