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

from dao import Database
from typing import Callable

class TaskContext:

    def __init__(
            self,
            dao: Database,
            user_id: str|None=None,
            async_q: Callable|None=None,
            message_sender: Callable|None=None,
        ):
        self._dao = dao
        self._user_id = user_id
        self._async_q = async_q
        self._message_sender = message_sender


    @property
    def dao(self) -> Database:
        return self._dao

    @property
    def user_id(self) -> str|None:
        return self._user_id

    def queue_async(self, fn, *args, **kwargs):
        if not self._async_q:
            raise TaskException("No task enqueuer defined")
        self._async_q(fn, *args, **kwargs)

    def send_message(self, name: str, payload):
        if not self._message_sender:
            raise TaskException("No message sender defined")
        self._message_sender(name, payload)

class TaskException(BaseException):
    def __init__(self, message: str, *args: object) -> None:
        super().__init__(*args)
        self._message = message

    @property
    def message(self) -> str|None:
        return self._message
