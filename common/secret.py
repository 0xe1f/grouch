import base64
import hashlib
import hmac
import json
import secrets

key = secrets.token_bytes()

def obfuscate_json(payload: object) -> str:
    payload_json = json.dumps(payload).encode()
    m = hmac.new(key, digestmod=hashlib.blake2b)
    m.update(payload_json)
    mac = m.digest()

    payload_b64 = base64.b64encode(payload_json).decode('ascii')
    mac_b64 = base64.b64encode(mac).decode('ascii')

    return f"{payload_b64}#{mac_b64}"

def deobfuscate_json(obfusc: str) -> object:
    split = obfusc.split("#")
    if len(split) != 2:
        return None

    payload_b64, mac_b64 = split[:2]
    payload_bytes = base64.b64decode(payload_b64)
    supplied_mac = base64.b64decode(mac_b64)

    m = hmac.new(key, digestmod=hashlib.blake2b)
    m.update(payload_bytes)
    computed_mac = m.digest()

    if not hmac.compare_digest(supplied_mac, computed_mac):
        return None

    # If we get to this point, it's fine to fail if JSON is invalid
    # (we generated it, so shouldn't happen)
    return json.loads(payload_bytes)
