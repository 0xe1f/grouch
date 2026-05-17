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

from os.path import abspath, dirname, exists, join
import flask_socketio
import tomllib

_socketio = None


def notify(user_id: str, event: str, payload=None):
    global _socketio
    if _socketio is None:
        config_path = "config.toml"
        if not exists(config_path):
            config_path = join(dirname(abspath(__file__)), "..", "config.toml")
        with open(config_path, "rb") as f:
            config = tomllib.load(f)
        _socketio = flask_socketio.SocketIO(message_queue=config['REDIS_URL'])
    _socketio.emit(event, payload, to=user_id)
