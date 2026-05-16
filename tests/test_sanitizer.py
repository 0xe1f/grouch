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

from parser.sanitizer import extract_text
from parser.sanitizer import sanitize_html
import unittest

class TestExtractText(unittest.TestCase):

    def test_strips_tags(self):
        self.assertEqual("Hello world", extract_text("<p>Hello <b>world</b></p>"))

    def test_strips_nested_tags(self):
        self.assertEqual("onetwothree", extract_text("<div><p>one</p><ul><li>two</li><li>three</li></ul></div>"))

    def test_collapses_whitespace(self):
        self.assertEqual("a b c", extract_text("<p>a   b\t\tc</p>"))

    def test_collapses_newlines(self):
        self.assertEqual("line one line two", extract_text("<p>line one\nline two</p>"))

    def test_strips_leading_trailing_whitespace(self):
        self.assertEqual("hello", extract_text("  <p>  hello  </p>  "))

    def test_unescapes_amp(self):
        self.assertEqual("a & b", extract_text("<p>a &amp; b</p>"))

    def test_unescapes_lt_gt(self):
        self.assertEqual("a < b > c", extract_text("<p>a &lt; b &gt; c</p>"))

    def test_unescapes_numeric_entity(self):
        self.assertEqual("©", extract_text("<p>&#169;</p>"))

    def test_max_len_truncates(self):
        result = extract_text("<p>Hello world</p>", max_len=5)
        self.assertEqual("Hello", result)

    def test_max_len_after_unescape(self):
        # "&amp;" is 5 chars in HTML but 1 char after unescaping.
        # Truncation should happen after unescaping, so max_len=3 on
        # "a &amp; b" (→ "a & b") should yield "a &" not "a &a"
        result = extract_text("<p>a &amp; b</p>", max_len=3)
        self.assertEqual("a &", result)

    def test_max_len_none_returns_full(self):
        self.assertEqual("Hello world", extract_text("<p>Hello world</p>", max_len=None))

    def test_max_len_larger_than_content(self):
        self.assertEqual("Hello", extract_text("<p>Hello</p>", max_len=100))

    def test_falsy_none_returns_none(self):
        self.assertIsNone(extract_text(None))

    def test_falsy_empty_string_returns_empty(self):
        self.assertEqual("", extract_text(""))

    def test_plain_text_passthrough(self):
        self.assertEqual("just text", extract_text("just text"))


class TestSanitizeHtml(unittest.TestCase):

    def test_removes_script_tag(self):
        result = sanitize_html("<p>Hello</p><script>alert(1)</script>")
        self.assertNotIn("<script>", result)
        self.assertNotIn("alert", result)

    def test_removes_style_tag(self):
        result = sanitize_html("<p>Hello</p><style>body{color:red}</style>")
        self.assertNotIn("<style>", result)

    def test_keeps_allowed_block_tags(self):
        result = sanitize_html("<p>paragraph</p>")
        self.assertIn("<p>", result)
        self.assertIn("paragraph", result)

    def test_keeps_allowed_inline_tags(self):
        result = sanitize_html("<p><strong>bold</strong> and <em>italic</em></p>")
        self.assertIn("<strong>", result)
        self.assertIn("<em>", result)

    def test_keeps_anchor_tag(self):
        result = sanitize_html('<p><a href="https://example.com">link</a></p>')
        self.assertIn("<a", result)
        self.assertIn("link", result)

    def test_falsy_none_returns_none(self):
        self.assertIsNone(sanitize_html(None))

    def test_falsy_empty_string_returns_empty(self):
        self.assertEqual("", sanitize_html(""))
