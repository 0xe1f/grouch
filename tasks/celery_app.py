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
from celery.signals import worker_process_init
from common.config import load_config
import dao
import functools
import redis as redis_lib


_config = load_config()

celery_app = Celery(
    'grouch',
    broker=_config['REDIS_URL'],
    backend=_config['REDIS_URL'],
    include=[
        'tasks.subscriptions',
        'tasks.articles',
        'tasks.folders',
        'tasks.favicons',
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
        raise RuntimeError("Worker not initialized — get_dao() called before worker init")
    return _dao


def get_redis() -> redis_lib.Redis:
    return _redis


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


def _init_dao(**kwargs):
    # Prefork children need their own connection (worker_init alone is parent-only).
    global _dao
    if _dao is not None:
        return
    conn = dao.Connection()
    conn.connect(
        _config['DATABASE_NAME'],
        _config['DATABASE_USERNAME'],
        _config['DATABASE_PASSWORD'],
        _config['DATABASE_HOSTNAME'],
        _config.get('DATABASE_PORT'),
    )
    _dao = dao.Database(conn.db)


@worker_init.connect
def init_worker(**kwargs):
    _init_dao(**kwargs)


@worker_process_init.connect
def init_worker_process(**kwargs):
    global _dao
    # After fork the parent's handle is unsafe; always reconnect in the child.
    _dao = None
    _init_dao(**kwargs)
