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

from web.ext_type.objects import Article
from web.ext_type.objects import JsonObject
from web.ext_type.objects import TableOfContents

class ArticlesResponse(JsonObject):

    def __init__(self, articles: list[Article]=[], next_start: str|None=None):
        super().__init__(
            {
                "articles": [article.as_dict() for article in articles],
                "continue": next_start,
            }
        )

class CreateFolderResponse(JsonObject):

    def __init__(self, toc: TableOfContents):
        super().__init__(
            {
                "subscriptions": toc.as_dict(),
            },
        )

class DeleteFolderResponse(JsonObject):

    def __init__(self, toc: TableOfContents):
        super().__init__(
            {
                "subscriptions": toc.as_dict(),
            },
        )

class ImportFeedsResponse(JsonObject):

    def __init__(self):
        super().__init__()

class MarkAllAsReadResponse(JsonObject):

    def __init__(self, toc: TableOfContents):
        super().__init__(
            {
                "subscriptions": toc.as_dict(),
            },
        )

class MoveSubResponse(JsonObject):

    def __init__(self, toc: TableOfContents):
        super().__init__(
            {
                "subscriptions": toc.as_dict(),
            },
        )

class RemoveTagResponse(JsonObject):

    def __init__(self, toc: TableOfContents):
        super().__init__(
            {
                "subscriptions": toc.as_dict(),
            },
        )

class RenameResponse(JsonObject):

    def __init__(self, toc: TableOfContents):
        super().__init__(
            {
                "subscriptions": toc.as_dict(),
            },
        )

class SetTagsResponse(JsonObject):

    def __init__(self, toc: TableOfContents, tags: list[str]):
        super().__init__(
            {
                "subscriptions": toc.as_dict(),
                "tags": tags,
            },
        )

class SubscribeResponse(JsonObject):

    def __init__(self):
        super().__init__()

class SyncFeedsResponse(JsonObject):

    def __init__(self, next_sync: str|None=None):
        super().__init__(
            {
                "nextSync": next_sync,
            },
        )

class UnsubscribeResponse(JsonObject):

    def __init__(self, toc: TableOfContents):
        super().__init__(
            {
                "subscriptions": toc.as_dict(),
            },
        )
