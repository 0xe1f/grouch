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
