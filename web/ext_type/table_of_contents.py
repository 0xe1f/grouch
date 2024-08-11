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

from web.ext_type.json_object import JsonObject
from web.ext_type.folder import Folder
from web.ext_type.subscription import Subscription
from web.ext_type.tag import Tag

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
