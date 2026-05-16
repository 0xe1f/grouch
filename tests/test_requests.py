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

from web.ext_type.objects import ValidationException
from web.ext_type.requests import CreateAccountRequest
from web.ext_type.requests import LoginRequest
import unittest

_VALID_ACCOUNT = {
    "username": "testuser",
    "email_address": "test@example.com",
    "password": "password123",
    "confirm_password": "password123",
}


class TestLoginRequestValidation(unittest.TestCase):

    def test_passes_with_both_fields(self):
        req = LoginRequest({"username": "user", "password": "pass"})
        req.validate()

    def test_raises_without_username(self):
        req = LoginRequest({"password": "pass"})
        with self.assertRaises(ValidationException):
            req.validate()

    def test_raises_without_password(self):
        req = LoginRequest({"username": "user"})
        with self.assertRaises(ValidationException):
            req.validate()

    def test_raises_with_empty_username(self):
        req = LoginRequest({"username": "", "password": "pass"})
        with self.assertRaises(ValidationException):
            req.validate()

    def test_raises_with_empty_password(self):
        req = LoginRequest({"username": "user", "password": ""})
        with self.assertRaises(ValidationException):
            req.validate()


class TestCreateAccountRequestValidation(unittest.TestCase):

    def _make(self, overrides: dict={}):
        data = {**_VALID_ACCOUNT, **overrides}
        return CreateAccountRequest(data)

    def test_passes_with_valid_data(self):
        self._make().validate()

    def test_raises_without_username(self):
        with self.assertRaises(ValidationException):
            self._make({"username": ""}).validate()

    def test_raises_without_email(self):
        with self.assertRaises(ValidationException):
            self._make({"email_address": ""}).validate()

    def test_raises_without_password(self):
        with self.assertRaises(ValidationException):
            self._make({"password": "", "confirm_password": ""}).validate()

    def test_raises_on_invalid_email_no_at(self):
        with self.assertRaises(ValidationException):
            self._make({"email_address": "notanemail"}).validate()

    def test_raises_on_invalid_email_no_domain(self):
        with self.assertRaises(ValidationException):
            self._make({"email_address": "user@"}).validate()

    def test_raises_on_invalid_email_no_tld(self):
        with self.assertRaises(ValidationException):
            self._make({"email_address": "user@domain"}).validate()

    def test_accepts_valid_email_formats(self):
        for email in [
            "user@example.com",
            "user+tag@example.co.uk",
            "first.last@sub.domain.org",
        ]:
            with self.subTest(email=email):
                self._make({"email_address": email}).validate()

    def test_raises_when_password_too_short(self):
        with self.assertRaises(ValidationException):
            self._make({"password": "short", "confirm_password": "short"}).validate()

    def test_raises_when_passwords_dont_match(self):
        with self.assertRaises(ValidationException):
            self._make({"confirm_password": "different"}).validate()

    def test_passes_at_minimum_password_length(self):
        pw = "exactly8"
        self._make({"password": pw, "confirm_password": pw}).validate()
