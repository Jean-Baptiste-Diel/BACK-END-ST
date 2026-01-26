import requests
import time
import uuid
import hashlib
from flask import Blueprint, jsonify, request, current_app

bp_camera = Blueprint("camera", __name__)

APP_ID = "lcea5699cd1d7c4457"
APP_SECRET = "f464f4b27e934bcba36125d953a4c6"
DATACENTER = "fk"

# ===============================
# 🔐 CACHE TOKEN IMOU
# ===============================
IMOU_TOKEN_CACHE = {
    "accessToken": None,
    "domain": None,
    "expires_at": 0
}

# ===============================
# 🔧 SIGN
# ===============================
def generate_sign():
    timestamp = int(time.time())
    nonce = str(uuid.uuid4())
    raw = f"time:{timestamp},nonce:{nonce},appSecret:{APP_SECRET}"
    sign = hashlib.md5(raw.encode()).hexdigest()
    return timestamp, nonce, sign

# ===============================
# 🔐 TOKEN INTERNE (UTILITAIRE)
# ===============================
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

    current_app.logger.info("🔐 Nouveau token Imou")

    return token, domain

# ===============================
# 🔐 ROUTE TOKEN (POUR FLUTTER)
# ===============================
@bp_camera.route("/get-token", methods=["GET"])
def get_token_route():
    try:
        token, domain = get_imou_token()
        return jsonify({
            "accessToken": token,
            "currentDomain": domain
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ===============================
# 📷 LIST DEVICES
# ===============================
@bp_camera.route("/devices", methods=["GET"])
def list_devices():
    try:
        token, _ = get_imou_token()
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
            "params": {
                "token": token,
                "page": 1,
                "pageSize": 50,
                "source": "bindAndShare"
            }
        }

        url = f"https://openapi-{DATACENTER}.easy4ip.com/openapi/listDeviceDetailsByPage"
        r = requests.post(url, json=body, timeout=10)
        data = r.json()

        if data.get("result", {}).get("code") != "0":
            return jsonify(data), 400

        devices = []

        for d in data["result"]["data"]["deviceList"]:
            channels = [
                {
                    "channelId": c.get("channelId", 0),
                    "channelName": c.get("channelName", "Main"),
                    "status": c.get("status"),
                    "ptz": c.get("channelId") == 0
                }
                for c in (d.get("channels") or [])
            ] or [{
                "channelId": 0,
                "channelName": "Main",
                "status": d.get("deviceStatus"),
                "ptz": True
            }]

            devices.append({
                "deviceId": d["deviceId"],
                "deviceName": d["deviceName"],
                "productId": d["productId"],
                "deviceStatus": d["deviceStatus"],
                "playToken": (d.get("playToken") or "").replace(" ", ""),
                "channels": channels
            })

        return jsonify(devices), 200

    except Exception as e:
        current_app.logger.exception(e)
        return jsonify({"error": "Erreur serveur"}), 500

# ===============================
# 🎮 PTZ
# ===============================
@bp_camera.route("/ptz", methods=["POST"])
def ptz():
    try:
        data = request.json
        token, _ = get_imou_token()

        operation_map = {
            "up": "0", "down": "1", "left": "2", "right": "3",
            "up_left": "4", "down_left": "5",
            "up_right": "6", "down_right": "7",
            "zoom_in": "8", "zoom_out": "9", "stop": "10"
        }

        operation = operation_map.get(data["direction"])
        if operation is None:
            return jsonify({"error": "Direction invalide"}), 400

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
            "params": {
                "token": token,
                "deviceId": data["deviceId"],
                "channelId": data.get("channelId", "0"),
                "operation": operation,
                "duration": "300"
            }
        }

        url = f"https://openapi-{DATACENTER}.easy4ip.com/openapi/controlMovePTZ"
        r = requests.post(url, json=body, timeout=10)

        return jsonify(r.json()), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
