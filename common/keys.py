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

import re

def build_key(prefix: str, *entity_ids: str) -> str:
    # Remove entity prefix from each key
    stripped = [re.sub(r"^[a-z]+::", "", id) for id in entity_ids]
    # Join them together and tack on a prefix
    return f"{prefix}::{"::".join(stripped)}"

def decompose_key(key: str) -> tuple[str|None, list[str]|None]:
    parts = key.split("::")
    if not parts:
        return None, None
    return parts[0], parts[1:]
