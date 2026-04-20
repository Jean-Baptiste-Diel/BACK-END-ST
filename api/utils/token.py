import hmac
import os
import time
import uuid
import hashlib
import requests
from flask import current_app

# IDENTIFIANTS IMOU
APP_ID = os.environ.get("APP_ID")
APP_SECRET = os.environ.get("APP_SECRET")
DATACENTER = os.environ.get("DATACENTER")
# IDENTIFIANTS TUYA
APP_ID_POMPE = os.environ.get("APP_ID_POMPE")
CLIENT_SECRET = os.environ.get("SECRET_KEY_POMPE")
BASE_URL_TUYA = os.environ.get("BASE_URL_TUYA")
# IDENTIFIANTS VANNE
APP_ID_VANNE=os.environ.get("APP_ID_VANNE")
APP_SECRET_VANNE=os.environ.get("APP_SECRET_VANNE")

# CACHE TOKEN IMOU
IMOU_TOKEN_CACHE = {
    "accessToken": None,
    "domain": None,
    "expires_at": 0
}
# CACHE TOKEN VANNE
VANNE_TOKEN_CACHE = {
    "token": None,
    "expires_at": 0
}
# SIGN GENERATE OF IMOU
def generate_sign():
    timestamp = int(time.time())
    nonce = str(uuid.uuid4())
    raw = f"time:{timestamp},nonce:{nonce},appSecret:{APP_SECRET}"
    sign = hashlib.md5(raw.encode()).hexdigest()
    return timestamp, nonce, sign
# SIGN GENERATE OF TUYA
    # UTIL SHA256
def sha256(content: str):
    return hashlib.sha256(content.encode("utf-8")).hexdigest()
def generate_sign_tuya():
    t = str(int(time.time() * 1000))

    method = "GET"
    path = "/v1.0/token?grant_type=1"
    body = ""

    body_hash = sha256(body)

    string_to_sign = f"{method}\n{body_hash}\n\n{path}"

    sign_str = APP_ID_POMPE + t + string_to_sign

    sign = hmac.new(
        CLIENT_SECRET.encode("utf-8"),
        sign_str.encode("utf-8"),
        hashlib.sha256
    ).hexdigest().upper()

    return t, sign, path
# GET TOKEN TUYA
def get_tuya_token():
    t, sign, path = generate_sign_tuya()

    headers = {
        "client_id": APP_ID_POMPE,
        "sign": sign,
        "t": t,
        "sign_method": "HMAC-SHA256"
    }

    url = BASE_URL_TUYA + path

    response = requests.get(url, headers=headers)

    return response.json()
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

# TOKEN POUR LES VANNES
def get_vanne_token():
    url = "http://smart1688.net/prod_api/open_api/anon/get_open_token"

    body = {
        'params': {
        "appId": APP_ID_VANNE,
        "appSecretKey": APP_SECRET_VANNE
    }
    }

    print("Request body:", body)

    try:
        r = requests.post(url, json=body, timeout=10)
        print("Status:", r.status_code)
        print("Response:", r.text)
        data = r.json()

        if data.get("tx_code") != "00":
            # Retour plus lisible pour l'utilisateur
            return {"error": data.get("error_info", {}), "status": "fail"}

        token = data["data"]["open_token"]
        return {"token": token, "status": "success"}

    except requests.exceptions.RequestException as e:
        return {"error": str(e), "status": "fail"}
# REFRESH TOKEN VANNE
def refresh_vanne_token():
    """
    Force récupération d'un nouveau token depuis smart1688
    """

    url = "http://smart1688.net/prod_api/open_api/anon/get_open_token"

    body = {
        "params": {
            "appId": APP_ID_VANNE,
            "appSecretKey": APP_SECRET_VANNE
        }
    }

    try:
        r = requests.post(url, json=body, timeout=10)
        data = r.json()

        print("VANNE TOKEN RESPONSE:", data)

        if data.get("tx_code") != "00":
            return {"status": "fail", "error": data}

        token = data["data"]["open_token"]

        expires_in = data["data"].get("expire_time", 3600)
        now = int(time.time())

        VANNE_TOKEN_CACHE["token"] = token
        VANNE_TOKEN_CACHE["expires_at"] = now + int(expires_in) - 60

        return {
            "status": "success",
            "token": token
        }

    except Exception as e:
        return {
            "status": "fail",
            "error": str(e)
        }
# GET TOKEN (CACHE + AUTO REFRESH)
def get_vanne_token():
    now = int(time.time())

    # si token encore valide
    if (
        VANNE_TOKEN_CACHE["token"]
        and now < VANNE_TOKEN_CACHE["expires_at"]
    ):
        return {
            "status": "success",
            "token": VANNE_TOKEN_CACHE["token"]
        }

    # sinon refresh
    return refresh_vanne_token()
# CLEAR TOKEN (OPTIONNEL)
def clear_vanne_token():
    VANNE_TOKEN_CACHE["token"] = None
    VANNE_TOKEN_CACHE["expires_at"] = 0