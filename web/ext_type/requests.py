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

from web.ext_type.objects import JsonObject

class ArticlesRequest(JsonObject):

    def __init__(self, source: dict[str, str]={}):
        super().__init__(source)

    @property
    def start(self) -> str:
        return self.get_prop("start")

    @property
    def folder(self) -> str:
        return self.get_prop("folder")

    @property
    def prop(self) -> str:
        return self.get_prop("prop")

    @property
    def sub(self) -> str:
        return self.get_prop("sub")

    @property
    def tag(self) -> str:
        return self.get_prop("tag")

class CreateFolderRequest(JsonObject):

    def __init__(self, source: dict[str, str]={}):
        super().__init__(source)

    @property
    def title(self) -> str:
        return self.get_prop("title")

class DeleteFolderRequest(JsonObject):

    def __init__(self, source: dict[str, str]={}):
        super().__init__(source)

    @property
    def id(self) -> str:
        return self.get_prop("id")

class MarkAllAsReadRequest(JsonObject):

    SCOPE_ALL = "all"
    SCOPE_SUB = "subscription"
    SCOPE_FOLDER = "folder"

    def __init__(self, source: dict[str, str]={}):
        super().__init__(source)

    @property
    def id(self) -> str:
        return self.get_prop("id")

    @property
    def scope(self) -> str:
        return self.get_prop("scope")

class MoveSubRequest(JsonObject):

    def __init__(self, source: dict[str, str]={}):
        super().__init__(source)

    @property
    def id(self) -> str:
        return self.get_prop("id")

    @property
    def destination(self) -> str:
        return self.get_prop("destination")

class RemoveTagRequest(JsonObject):

    def __init__(self, source: dict[str, str]={}):
        super().__init__(source)

    @property
    def tag(self) -> str:
        return self.get_prop("tag")

class RenameRequest(JsonObject):

    def __init__(self, source: dict={}):
        super().__init__(source)

    @property
    def id(self) -> str:
        return self.get_prop("id")

    @property
    def title(self) -> str:
        return self.get_prop("title")

class SetPropertyRequest(JsonObject):

    def __init__(self, source: dict[str, str]={}):
        super().__init__(source)

    @property
    def article_id(self) -> str:
        return self.get_prop("article")

    @property
    def prop_name(self) -> str:
        return self.get_prop("property")

    @property
    def is_set(self) -> bool:
        return self.get_prop("set")

class SetTagsRequest(JsonObject):

    def __init__(self, source: dict[str, str]={}):
        super().__init__(source)

    @property
    def article_id(self) -> str:
        return self.get_prop("articleId")

    @property
    def tags(self) -> list[str]:
        return self.get_prop("tags")

class SubscribeRequest(JsonObject):

    def __init__(self, source: dict[str, str]={}):
        super().__init__(source)

    @property
    def url(self) -> str:
        return self.get_prop("url")

    @property
    def folder_id(self) -> str:
        return self.get_prop("folderId")

class UnsubscribeRequest(JsonObject):

    def __init__(self, source: dict[str, str]={}):
        super().__init__(source)

    @property
    def id(self) -> str:
        return self.get_prop("id")
