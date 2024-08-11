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

from tasks.articles import move_articles
from tasks.articles import remove_tag_from_articles
from tasks.feeds import import_feeds
from tasks.feeds import refresh_feeds
from tasks.folders import delete_folder
from tasks.subscriptions import subscribe_user
from tasks.subscriptions import unsubscribe
from tasks.subscriptions import sync_subs
from tasks.subscriptions import mark_sub_read
from tasks.subscriptions import mark_subs_read_by_folder
from tasks.subscriptions import mark_subs_read_by_user
