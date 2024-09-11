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

from dao import Connection
from dao import Database
from datetime import datetime
from entity import Entity
import random
import tomllib
import unittest
import uuid

class TestEntity(Entity):

    DOC_TYPE = "test"

    def __init__(self, source: dict={}):
        super().__init__(source)
        if not source:
            self.doc_type = self.__class__.DOC_TYPE
            self.uid = TestDao.random_string()

    @property
    def uid(self) -> str:
        return self.get_prop("uid")

    @uid.setter
    def uid(self, val: str):
        self.set_prop("uid", val)

    @property
    def test(self) -> str:
        return self.get_prop("test")

    @test.setter
    def test(self, val: str):
        self.set_prop("test", val)

    def new_key(self) -> str|None:
        return self.build_key(self.doc_type, self.uid)

class TestDao(unittest.TestCase):

    TEST_DB_NAME = "test__test"

    def setUp(self):
        self._conn = Connection()

        with open("config.toml", "rb") as file:
            config = tomllib.load(file)

        self._conn.connect(
            __class__.TEST_DB_NAME,
            config["DATABASE_USERNAME"],
            config["DATABASE_PASSWORD"],
            config["DATABASE_HOST"],
            config.get("DATABASE_PORT"),
        )
        self._dao = Database(self._conn.db)

    def tearDown(self):
        self._conn.destroy()

    @property
    def connection(self):
        return self._conn

    @property
    def dao(self):
        return self._dao

    @classmethod
    def random_string(cls) -> str:
        return uuid.uuid4().hex

    @classmethod
    def random_timestamp(cls, jitter: int=0, factor: int=1) -> int:
        return datetime.now().timestamp() + random.randint(-jitter // 2, jitter // 2) * factor

    @classmethod
    def new_test(cls) -> TestEntity:
        test = TestEntity()
        test.test = cls.random_string()

        return test

    @classmethod
    def new_tests(cls, count: int) -> list[TestEntity]:
        tests = []
        for _ in range(count):
            test = TestEntity()
            test.test = cls.random_string()
            tests.append(test)

        return tests
