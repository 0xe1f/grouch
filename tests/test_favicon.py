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

from entity.favicon import Favicon
from entity.favicon import STATUS_MISSING
from entity.favicon import STATUS_OK
from io import BytesIO
from parser import favicon as favicon_mod
from parser.favicon import DISPLAY_SIZE
from parser.favicon import MAX_BYTES
from parser.favicon import build_display_png
from parser.favicon import hash_bytes
from PIL import Image
from entity.favicon import is_favicon_due
import base64
import time
import unittest


def _png_bytes(size: int, color=(255, 0, 0, 255)) -> bytes:
    img = Image.new("RGBA", (size, size), color)
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


class TestBuildDisplayPng(unittest.TestCase):

    def test_small_raster_not_upscaled(self):
        src = _png_bytes(16)
        display = build_display_png(src, "image/png")
        self.assertIsNotNone(display)
        self.assertEqual((display.width, display.height), (16, 16))
        self.assertTrue(display.content_hash)

    def test_large_raster_downscaled(self):
        src = _png_bytes(120)
        display = build_display_png(src, "image/png")
        self.assertIsNotNone(display)
        self.assertLessEqual(display.width, DISPLAY_SIZE)
        self.assertLessEqual(display.height, DISPLAY_SIZE)
        self.assertEqual(max(display.width, display.height), DISPLAY_SIZE)

    def test_oversized_edge_rejected(self):
        src = _png_bytes(600)
        self.assertIsNone(build_display_png(src, "image/png"))

    def test_oversized_bytes_rejected_in_acceptable(self):
        data = b"x" * (MAX_BYTES + 1)
        self.assertFalse(favicon_mod._acceptable_payload(data, "image/png"))

    def test_data_url_png(self):
        raw = _png_bytes(32)
        data_url = "data:image/png;base64," + base64.b64encode(raw).decode()
        source = favicon_mod._parse_data_url(data_url)
        self.assertIsNotNone(source)
        display = build_display_png(source.data, source.content_type)
        self.assertIsNotNone(display)
        self.assertEqual((display.width, display.height), (32, 32))

    def test_svg_rasterized_when_cairosvg_available(self):
        if favicon_mod.cairosvg is None:
            self.skipTest("cairosvg not installed")
        svg = b'<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10"><rect width="10" height="10" fill="red"/></svg>'
        display = build_display_png(svg, "image/svg+xml")
        self.assertIsNotNone(display)
        self.assertEqual((display.width, display.height), (DISPLAY_SIZE, DISPLAY_SIZE))

    def test_hash_stable(self):
        data = _png_bytes(8)
        self.assertEqual(hash_bytes(data), hash_bytes(data))


class TestFaviconEntity(unittest.TestCase):

    def test_key_from_feed_id(self):
        fav = Favicon()
        fav.feed_id = "feed::http://example.com/rss"
        key = fav.new_key()
        self.assertTrue(key.startswith("favicon::"))
        self.assertEqual(key, Favicon.build_key(Favicon.DOC_TYPE, fav.feed_id))


class TestFaviconDue(unittest.TestCase):

    def test_missing_doc_due(self):
        self.assertTrue(is_favicon_due(None))

    def test_ok_recent_not_due(self):
        fav = Favicon()
        fav.status = STATUS_OK
        fav.checked_at = time.time()
        fav._doc["_attachments"] = {"display": {"stub": True}}
        self.assertFalse(is_favicon_due(fav))

    def test_ok_old_due(self):
        fav = Favicon()
        fav.status = STATUS_OK
        fav.checked_at = time.time() - (31 * 86400)
        fav._doc["_attachments"] = {"display": {"stub": True}}
        self.assertTrue(is_favicon_due(fav))

    def test_missing_recent_not_due(self):
        fav = Favicon()
        fav.status = STATUS_MISSING
        fav.checked_at = time.time()
        self.assertFalse(is_favicon_due(fav))

    def test_missing_old_due(self):
        fav = Favicon()
        fav.status = STATUS_MISSING
        fav.checked_at = time.time() - (8 * 86400)
        self.assertTrue(is_favicon_due(fav))


if __name__ == "__main__":
    unittest.main()
