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
from web.ext_type.objects import ValidationException
import re

class RequestObject(JsonObject):

    def __init__(self, source: dict[str, str]={}):
        super().__init__(source)

    def validate(self):
        pass

class ArticlesRequest(RequestObject):

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

class CreateFolderRequest(RequestObject):

    def __init__(self, source: dict[str, str]={}):
        super().__init__(source)

    @property
    def title(self) -> str:
        return self.get_prop("title")

class DeleteFolderRequest(RequestObject):

    def __init__(self, source: dict[str, str]={}):
        super().__init__(source)

    @property
    def id(self) -> str:
        return self.get_prop("id")

class MarkAllAsReadRequest(RequestObject):

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

class MoveSubRequest(RequestObject):

    def __init__(self, source: dict[str, str]={}):
        super().__init__(source)

    @property
    def id(self) -> str:
        return self.get_prop("id")

    @property
    def destination(self) -> str:
        return self.get_prop("destination")

class RemoveTagRequest(RequestObject):

    def __init__(self, source: dict[str, str]={}):
        super().__init__(source)

    @property
    def tag(self) -> str:
        return self.get_prop("tag")

class RenameRequest(RequestObject):

    def __init__(self, source: dict={}):
        super().__init__(source)

    @property
    def id(self) -> str:
        return self.get_prop("id")

    @property
    def title(self) -> str:
        return self.get_prop("title")

class SetPropertyRequest(RequestObject):

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

class SetTagsRequest(RequestObject):

    def __init__(self, source: dict[str, str]={}):
        super().__init__(source)

    @property
    def article_id(self) -> str:
        return self.get_prop("articleId")

    @property
    def tags(self) -> list[str]:
        return self.get_prop("tags")

class SubscribeRequest(RequestObject):

    def __init__(self, source: dict[str, str]={}):
        super().__init__(source)

    @property
    def url(self) -> str:
        return self.get_prop("url")

    @property
    def folder_id(self) -> str:
        return self.get_prop("folderId")

class UnsubscribeRequest(RequestObject):

    def __init__(self, source: dict[str, str]={}):
        super().__init__(source)

    @property
    def id(self) -> str:
        return self.get_prop("id")

class LoginRequest(RequestObject):

    def __init__(self, source: dict[str, str]={}):
        super().__init__(source)

    @property
    def username(self) -> str:
        return self.get_prop("username")

    @property
    def password(self) -> str:
        return self.get_prop("password")

    def validate(self):
        if not self.username:
            raise ValidationException("Missing username")
        if not self.password:
            raise ValidationException("Missing password")

class CreateAccountRequest(RequestObject):

    REGEX_EMAIL_ADDRESS = re.compile(
        r"(?:[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*|\"(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21\x23-\x5b\x5d-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])*\")@(?:(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?|\[(?:(?:(2(5[0-5]|[0-4][0-9])|1[0-9][0-9]|[1-9]?[0-9]))\.){3}(?:(2(5[0-5]|[0-4][0-9])|1[0-9][0-9]|[1-9]?[0-9])|[a-z0-9-]*[a-z0-9]:(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21-\x5a\x53-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])+)\])"
    )

    def __init__(self, source: dict[str, str]={}):
        super().__init__(source)

    @property
    def username(self) -> str:
        return self.get_prop("username")

    @property
    def email_address(self) -> str:
        return self.get_prop("email_address")

    @property
    def password(self) -> str:
        return self.get_prop("password")

    def validate(self):
        if not self.username:
            raise ValidationException("Missing username")
        if not self.email_address:
            raise ValidationException("Missing email address")
        if not self.__class__.REGEX_EMAIL_ADDRESS.fullmatch(self.email_address):
            raise ValidationException("Invalid email address")
        if not self.password:
            raise ValidationException("Missing password")
        if len(self.password) < 8:
            raise ValidationException("Passwords should contain at least 8 characters")
        if self.get_prop("confirm_password") != self.password:
            raise ValidationException("Passwords don't match")
