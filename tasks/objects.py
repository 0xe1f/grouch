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

from store import Connection
from typing import Callable

class TaskContext:

    def __init__(
            self,
            conn: Connection,
            user_id: str|None=None,
            session_id: str|None=None,
            async_q: Callable|None=None,
        ):
        self._conn = conn
        self._user_id = user_id
        self._session_id = session_id
        self._async_q = async_q

    @property
    def connection(self) -> str|None:
        return self._conn

    @property
    def session_id(self) -> str|None:
        return self._session_id

    @property
    def user_id(self) -> str|None:
        return self._user_id

    def queue_async(self, fn, *args, **kwargs):
        if not self._async_q:
            raise TaskException("No task enqueuer defined")
        self._async_q(fn, *args, **kwargs)

class TaskException(BaseException):
    def __init__(self, message: str, *args: object) -> None:
        super().__init__(*args)
        self._message = message

    @property
    def message(self) -> str|None:
        return self._message
