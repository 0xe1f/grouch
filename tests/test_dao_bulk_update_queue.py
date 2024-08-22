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

from dao import BulkUpdateQueue
from tests.test_dao import TestDao

class TestDaoBulkUpdateQueue(TestDao):

    def test_enqueue_count(self):
        with BulkUpdateQueue(self.connection.db, max_size=2) as bulk_q:
            bulk_q.enqueue(*self.new_tests(15))

        self.assertEqual(bulk_q.enqueued_count, 15)

    def test_conflict_count(self):
        tests = self.new_tests(15)
        with BulkUpdateQueue(self.connection.db) as bulk_q:
            bulk_q.enqueue(*tests)
        self.assertEqual(bulk_q.conflict_count, 0)

        # Remove revision (save as new object)
        for test in tests:
            test.rev = None

        bulk_q.enqueue(*tests)
        bulk_q.flush()

        self.assertEqual(bulk_q.conflict_count, 15)

    def test_enqueue_no_commit(self):
        with BulkUpdateQueue(self.connection.db, max_size=10) as bulk_q:
            bulk_q.enqueue(*self.new_tests(9))

            self.assertEqual(bulk_q.enqueued_count, 9)
            self.assertEqual(bulk_q.written_count, 0)

    def test_implicit_commit(self):
        with BulkUpdateQueue(self.connection.db, max_size=10) as bulk_q:
            bulk_q.enqueue(*self.new_tests(11))

            self.assertEqual(bulk_q.written_count, 10)
            self.assertEqual(bulk_q.commit_count, 1)

    def test_explicit_commit(self):
        with BulkUpdateQueue(self.connection.db, max_size=10) as bulk_q:
            bulk_q.enqueue(*self.new_tests(11))

        self.assertEqual(bulk_q.written_count, 11)
        self.assertEqual(bulk_q.commit_count, 2)

    def test_flush(self):
        bulk_q = BulkUpdateQueue(self.connection.db, max_size=10)
        bulk_q.enqueue(*self.new_tests(11))
        bulk_q.flush()

        self.assertEqual(bulk_q.written_count, 11)
        self.assertEqual(bulk_q.commit_count, 2)

    def test_rev_set(self):
        tests = self.new_tests(15)
        for test in tests:
            self.assertFalse(test.rev)

        with BulkUpdateQueue(self.connection.db) as bulk_q:
            bulk_q.enqueue(*tests)

        for test in tests:
            self.assertTrue(test.rev)

    def test_updated_set(self):
        tests = self.new_tests(15)
        for test in tests:
            self.assertFalse(test.updated)

        with BulkUpdateQueue(self.connection.db) as bulk_q:
            bulk_q.enqueue(*tests)

        for test in tests:
            self.assertTrue(test.updated)

    def test_id_tracking_enabled(self):
        tests = self.new_tests(15)
        with BulkUpdateQueue(self.connection.db, track_ids=True) as bulk_q:
            bulk_q.enqueue(*tests)

        test_ids = set([test.id for test in tests])
        written_ids = set(bulk_q.pop_written_ids())

        self.assertEqual(test_ids, written_ids)

    def test_id_tracking_disabled(self):
        tests = self.new_tests(15)
        with BulkUpdateQueue(self.connection.db, track_ids=True) as bulk_q:
            bulk_q.enqueue(*tests)

        self.assertEqual(len(bulk_q.pop_written_ids()), len(tests))
