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

from celery import Celery
from celery.signals import worker_init
from os.path import abspath, dirname, exists, join
import dao
import functools
import redis as redis_lib
import tomllib


def _load_config() -> dict:
    config_path = "config.toml"
    if not exists(config_path):
        config_path = join(dirname(abspath(__file__)), "..", "config.toml")
    with open(config_path, "rb") as f:
        return tomllib.load(f)


_config = _load_config()

celery_app = Celery(
    'grouch',
    broker=_config['REDIS_URL'],
    backend=_config['REDIS_URL'],
    include=[
        'tasks.subscriptions',
        'tasks.articles',
        'tasks.folders',
    ],
)

celery_app.conf.update(
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    result_expires=3600,
)

_dao: dao.Database | None = None
_redis = redis_lib.Redis.from_url(_config['REDIS_URL'])


def get_dao() -> dao.Database:
    if _dao is None:
        raise RuntimeError("Worker not initialized — get_dao() called before @worker_init")
    return _dao


def per_user(func):
    @functools.wraps(func)
    def wrapper(self, user_id: str, *args, **kwargs):
        if not _redis.set(f"user_lock:{user_id}", self.request.id, nx=True, ex=600):
            raise self.retry()
        try:
            return func(self, user_id, *args, **kwargs)
        finally:
            _redis.delete(f"user_lock:{user_id}")
    return wrapper


@worker_init.connect
def init_worker(**kwargs):
    global _dao
    conn = dao.Connection()
    conn.connect(
        _config['DATABASE_NAME'],
        _config['DATABASE_USERNAME'],
        _config['DATABASE_PASSWORD'],
        _config['DATABASE_HOST'],
        _config.get('DATABASE_PORT'),
        use_tls=_config.get('DATABASE_USE_TLS', False),
    )
    _dao = dao.Database(conn.db)
