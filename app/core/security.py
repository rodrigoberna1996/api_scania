import hashlib
import hmac
import base64

def base64url_encode(arg: bytes) -> str:
    s = base64.b64encode(arg).decode("utf-8")
    s = s.rstrip("=")
    s = s.replace("+", "-")
    s = s.replace("/", "_")
    return s

def base64url_decode(arg: str) -> bytes:
    s = arg
    s = s.replace("-", "+")
    s = s.replace("_", "/")
    strlen = len(s) % 4
    if strlen == 2:
        s += "=="
    elif strlen == 3:
        s += "="
    elif strlen != 0:
        raise ValueError("Illegal base64Url string")
    return base64.b64decode(s)

def create_challenge_response(secret_key: str, challenge: str) -> str:
    secret_key_bytes = base64url_decode(secret_key)
    challenge_bytes = base64url_decode(challenge)
    hmac_digest = hmac.new(secret_key_bytes, challenge_bytes, hashlib.sha256).digest()
    return base64url_encode(hmac_digest)
