import os
import time
import uuid
import hashlib
import requests
from flask import current_app

APP_ID = os.environ.get("APP_ID")
APP_SECRET = os.environ.get("APP_SECRET")
DATACENTER = os.environ.get("DATACENTER")

# CACHE TOKEN IMOU
IMOU_TOKEN_CACHE = {
    "accessToken": None,
    "domain": None,
    "expires_at": 0
}

# SIGN
def generate_sign():
    timestamp = int(time.time())
    nonce = str(uuid.uuid4())
    raw = f"time:{timestamp},nonce:{nonce},appSecret:{APP_SECRET}"
    sign = hashlib.md5(raw.encode()).hexdigest()
    return timestamp, nonce, sign

# TOKEN INTERNE (UTILITAIRE)
def get_imou_token():
    now = int(time.time())
    if (
        IMOU_TOKEN_CACHE["accessToken"]
        and now < IMOU_TOKEN_CACHE["expires_at"]
    ):
        return IMOU_TOKEN_CACHE["accessToken"], IMOU_TOKEN_CACHE["domain"]
    timestamp, nonce, sign = generate_sign()

    body = {
        "system": {
            "ver": "1.0",
            "appId": APP_ID,
            "sign": sign,
            "time": timestamp,
            "nonce": nonce
        },
        "id": str(uuid.uuid4()),
        "params": {}
    }

    url = f"https://openapi-{DATACENTER}.easy4ip.com/openapi/accessToken"
    r = requests.post(url, json=body, timeout=5)
    data = r.json()

    if data.get("result", {}).get("code") != "0":
        raise Exception(data)

    token = data["result"]["data"]["accessToken"]
    domain = (
        data["result"]["data"]["currentDomain"]
        .replace("https://", "")
        .replace("http://", "")
        .split(":")[0]
    )

    expire = int(data["result"]["data"]["expireTime"])

    IMOU_TOKEN_CACHE.update({
        "accessToken": token,
        "domain": domain,
        "expires_at": now + expire - 60
    })

    current_app.logger.info("Nouveau token Imou")

    return token, domain