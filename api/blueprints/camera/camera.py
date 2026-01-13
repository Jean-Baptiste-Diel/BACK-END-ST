import requests
import time
import uuid
import hashlib
from flask import Blueprint, jsonify, request
bp_camera = Blueprint("camera", __name__)

APP_ID = "lcea5699cd1d7c4457"
APP_SECRET = "f464f4b27e934bcba36125d953a4c6"
DATACENTER = "fk"

# FONCTION UTILE : GÉNÉRATION SIGN
def generate_sign():
    timestamp = int(time.time())
    nonce = str(uuid.uuid4())
    original = f"time:{timestamp},nonce:{nonce},appSecret:{APP_SECRET}"
    sign = hashlib.md5(original.encode("utf-8")).hexdigest()
    return timestamp, nonce, sign

# GET TOKEN
@bp_camera.route('/get-token', methods=['GET'])
def get_token():
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
    try:
        response = requests.post(url, json=body, timeout=10)
        data = response.json()
        print("Réponse brute Imou :", data)
        if "result" in data and data["result"]["code"] == "0":
            token = data["result"]["data"]["accessToken"]
            print("Access Token :", token)
            # On renvoie token + timestamp + nonce + sign
            return jsonify({
                "accessToken": token,
                "currentDomain": data["result"]["data"]["currentDomain"],
                "timestamp": timestamp,
                "nonce": nonce,
                "sign": sign
            })
        else:
            return jsonify({"error": "Impossible de récupérer le token", "response": data}), 400
    except requests.exceptions.RequestException as e:
        print("Erreur réseau :", e)
        return jsonify({"error": "Erreur réseau", "details": str(e)}), 500

#  LIST DEVICES
@bp_camera.route('/devices', methods=['GET'])
def list_devices():
    token_response = get_token()
    if token_response.status_code != 200:
        return token_response
    token = token_response.get_json()["accessToken"]
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
            "queryRange": "1-10"
        }
    }
    url = f"https://openapi-{DATACENTER}.easy4ip.com/openapi/liveList"
    try:
        response = requests.post(url, json=body, timeout=10)
        data = response.json()
        print("Réponse devices :", data)

        if "result" in data and data["result"]["code"] == "0":
            return jsonify(data["result"]["data"])
        else:
            return jsonify({"error": "Impossible de récupérer la liste des devices", "response": data}), 400

    except requests.exceptions.RequestException as e:
        print("Erreur réseau :", e)
        return jsonify({"error": "Erreur réseau", "details": str(e)}), 500

# GET LIVE URL
@bp_camera.route('/liveurl', methods=['GET'])
def get_live_url():
    device_serial = "A449DAKPSF9E4BA"
    token_response = get_token()
    if token_response.status_code != 200:
        return token_response
    token = token_response.get_json()["accessToken"]
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
            "deviceId": device_serial,
            "channelId": "0",
            "streamId": 0,
            "expireTime": 3600
        }
    }
    url = "https://openapi-fk.easy4ip.com/openapi/bindDeviceLive"
    try:
        response = requests.post(url, json=body, timeout=10)
        data = response.json()
        print("Réponse bindDeviceLive :", data)
        if "result" in data and data["result"]["code"] == "0":
            live_url = data["result"]["data"]["url"]
            return jsonify({"liveUrl": live_url})
        else:
            return jsonify({"error": data["result"]["msg"], "code": data["result"]["code"], "response": data}), 400
    except requests.exceptions.RequestException as e:
        print("Erreur réseau :", e)
        return jsonify({"error": "Erreur réseau", "details": str(e)}), 500




