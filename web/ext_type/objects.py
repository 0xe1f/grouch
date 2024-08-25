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

import entity
import datetime
import http

class JsonObject:

    def __init__(self, source: dict={}):
        self._doc = { k:v for k, v in source.items() if v != None }

    def get_prop(self, name: str, default: object=None) -> object:
        return self._doc.get(name, default)

    def set_prop(self, name: str, val: object):
        if val != None:
            self._doc[name] = val
        else:
            # Delete null values
            self._doc.pop(name, None)

    def __bool__(self):
        return not not self._doc

    def as_dict(self):
        return self._doc

class Article(JsonObject):

    # 	Media []*EntryMedia   `datastore:"-" json:"media,omitempty"`

    def __init__(self, article: entity.Article|None=None, entry: entity.Entry|None=None, source: dict={}):
        super().__init__(source)
        if article:
            self.set_prop("id", article.id)
            self.set_prop("properties", article.props)
            self.set_prop("tags", article.tags)
            self.set_prop("source", article.subscription_id)
        if entry:
            self.set_prop("link", entry.link)
            self.set_prop("title", entry.title)
            self.set_prop("author", entry.author)
            self.set_prop("summary", entry.text_summary)
            self.set_prop("content", entry.text_body)
            if published := entry.published:
                self.set_prop("published", datetime.datetime.fromtimestamp(published, datetime.UTC).isoformat())

    @property
    def id(self) -> str:
        return self._doc.get("id")

    @property
    def link(self) -> str:
        return self._doc.get("link")

    @property
    def title(self) -> str:
        return self._doc.get("title")

    @property
    def author(self) -> str:
        return self._doc.get("author")

    @property
    def summary(self) -> str:
        return self._doc.get("summary")

    @property
    def body(self) -> str:
        return self._doc.get("content")

    @property
    def tags(self) -> list[str]:
        return self._doc.get("tags")

    @property
    def props(self) -> list[str]:
        return self._doc.get("properties")

    @property
    def published(self) -> str:
        return self._doc.get("published")

    @property
    def subscription_id(self) -> str:
        return self._doc.get("source")

class Error(JsonObject):

    def __init__(self, message: str):
        super().__init__({})
        self.set_prop("message", message)

    @property
    def message(self) -> str:
        return self.get_prop("message")

    def as_dict(self):
        return super().as_dict(), http.HTTPStatus.BAD_REQUEST

class Folder(JsonObject):

    def __init__(self, folder: entity.Folder|None=None, source: dict={}):
        super().__init__(source)
        if folder:
            self.set_prop("id", folder.id)
            self.set_prop("title", folder.title)

    @property
    def id(self) -> str:
        return self._doc.get("id")

    @property
    def title(self) -> str:
        return self._doc.get("title")

class Subscription(JsonObject):

    def __init__(
        self,
        sub: entity.Subscription|None=None,
        feed: entity.Feed|None=None,
        unread_count: int|None=None,
        source: dict={},
    ):
        super().__init__(source)
        if sub:
            self.set_prop("id", sub.id)
            self.set_prop("title", sub.title)
            self.set_prop("parent", sub.folder_id)
        if feed:
            self.set_prop("faviconUrl", feed.favicon_url)
            self.set_prop("link", feed.site_url)
        self.set_prop("unread", unread_count or 0)

    @property
    def id(self) -> str:
        return self._doc.get("id")

    @property
    def link(self) -> str:
        return self._doc.get("link")

    @property
    def title(self) -> str:
        return self._doc.get("title")

    @property
    def unread_count(self) -> int:
        return self._doc.get("unread")

    @unread_count.setter
    def unread_count(self, val: int):
        self.set_prop("unread", val)

    @property
    def favicon_url(self) -> str:
        return self._doc.get("faviconUrl")

    @property
    def folder_id(self) -> str:
        return self._doc.get("parent")

class Tag(JsonObject):

    def __init__(self, tag: str|None=None, source: dict={}):
        super().__init__(source)
        if tag:
            self.set_prop("title", tag)

    @property
    def title(self) -> str:
        return self._doc.get("title")

class TableOfContents(JsonObject):

    def __init__(self, subs: list[Subscription]=[], folders: list[Folder]=[], tags: list[Tag]=[], source: dict={}):
        super().__init__(source)
        self.set_prop("subscriptions", [sub.as_dict() for sub in subs])
        self.set_prop("folders", [folder.as_dict() for folder in folders])
        self.set_prop("tags", [tag.as_dict() for tag in tags])

    @property
    def subscriptions(self) -> list[Subscription]:
        return [Subscription(source=sub) for sub in self.get_prop("subscriptions", [])]

    @property
    def folders(self) -> list[Folder]:
        return [Folder(source=folder) for folder in self.get_prop("folders", [])]

    @property
    def tags(self) -> list[Tag]:
        return [Tag(source=tag) for tag in self.get_prop("tags", [])]

    def remove_tag(self, tag_title: str):
        self.set_prop("tags", [tag.as_dict() for tag in self.tags if tag.title != tag_title])

    def remove_folder(self, folder_id: str):
        self.set_prop("folders", [folder.as_dict() for folder in self.folders if folder.id != folder_id])
        self.set_prop("subscriptions", [sub.as_dict() for sub in self.subscriptions if sub.folder_id != folder_id])

    def remove_subscription(self, sub_id: str):
        self.set_prop("subscriptions", [sub.as_dict() for sub in self.subscriptions if sub.id != sub_id])

    def mark_sub_as_read(self, sub_id: str):
        subs = []
        for sub in self.subscriptions:
            if sub.id == sub_id:
                sub.unread_count = 0
            subs.append(sub.as_dict())
        self.set_prop("subscriptions", subs)

    def mark_folder_as_read(self, folder_id: str):
        subs = []
        for sub in self.subscriptions:
            if sub.folder_id == folder_id:
                sub.unread_count = 0
            subs.append(sub.as_dict())
        self.set_prop("subscriptions", subs)

    def mark_all_as_read(self):
        subs = []
        for sub in self.subscriptions:
            sub.unread_count = 0
            subs.append(sub.as_dict())
        self.set_prop("subscriptions", subs)

class User(JsonObject):

    def __init__(self, user: entity.User|None=None, source: dict={}):
        super().__init__(source)
        if user:
            self.set_prop("id", user.id)
            self.set_prop("username", user.username)
            self.set_prop("email_address", user.email_address)

    @property
    def id(self) -> str:
        return self._doc.get("id")

    @property
    def username(self) -> str:
        return self._doc.get("username")

    @property
    def email_address(self) -> str:
        return self._doc.get("email_address")

    @property
    def is_authenticated(self) -> str:
        return not not self.id

    @property
    def is_active(self) -> str:
        return self.is_authenticated

    @property
    def is_anonymous(self) -> str:
        return not self.is_authenticated

    def get_id(self):
        return self._doc.get("id")

class ValidationException(BaseException):

    def __init__(self, message: str, *args: object) -> None:
        super().__init__(*args)
        self._message = message

    @property
    def message(self) -> str|None:
        return self._message
