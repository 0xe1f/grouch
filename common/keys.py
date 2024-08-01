import re


def build_key(prefix: str, *entity_ids: str) -> str:
    # Remove entity prefix from each key
    stripped = [re.sub(r"^[a-z]+::", "", id) for id in entity_ids]
    # Join them together and tack on a prefix
    return f"{prefix}::{"::".join(stripped)}"

