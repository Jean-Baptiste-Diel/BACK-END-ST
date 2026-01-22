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
            raw_domain = data["result"]["data"]["currentDomain"]

            # CORRECTION DOMAIN POUR ANDROID SDK
            clean_domain = (
                raw_domain
                .replace("https://", "")
                .replace("http://", "")
                .split(":")[0]
            )

            print("Access Token :", token)
            print("Domain brut :", raw_domain)
            print("Domain clean :", clean_domain)

            return jsonify({
                "accessToken": token,
                "currentDomain": clean_domain,
                "timestamp": timestamp,
                "nonce": nonce,
                "sign": sign
            })

        else:
            return jsonify({
                "error": "Impossible de récupérer le token",
                "response": data
            }), 400

    except requests.exceptions.RequestException as e:
        print("Erreur réseau :", e)
        return jsonify({
            "error": "Erreur réseau",
            "details": str(e)
        }), 500

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
            "page": 1,
            "pageSize": 50,
            "source": "bindAndShare"
        }
    }
    url = f"https://openapi-{DATACENTER}.easy4ip.com/openapi/listDeviceDetailsByPage"
    try:
        response = requests.post(url, json=body, timeout=10)
        data = response.json()
        if data.get("result", {}).get("code") != "0":
            return jsonify({
                "error": "Impossible de récupérer la liste des devices",
                "imouResponse": data
            }), 400
        devices = []
        for d in data["result"]["data"].get("deviceList", []):
            device_id = d.get("deviceId")
            product_id = d.get("productId")
            device_status = d.get("deviceStatus")

            play_token = (d.get("playToken") or "").replace(" ", "")

            raw_channels = d.get("channels") or []
            channels = []
            if product_id == "SC58X9BD":
                channels = [
                    {
                        "channelId": 0,
                        "channelName": "Lentille PT",
                        "status": "online",
                        "ptz": True
                    },
                    {
                        "channelId": 1,
                        "channelName": "Objectif fixe",
                        "status": "online",
                        "ptz": False
                    }
                ]
            else:
                if raw_channels:
                    for c in raw_channels:
                        channel_id = c.get("channelId", 0)
                        channels.append({
                            "channelId": channel_id,
                            "channelName": c.get("channelName", "Main"),
                            "status": c.get("status", device_status),
                            "ptz": channel_id == 0
                        })
                else:
                    # fallback sécurité
                    channels = [{
                        "channelId": 0,
                        "channelName": "Main",
                        "status": device_status,
                        "ptz": True
                    }]
            devices.append({
                "deviceId": device_id,
                "productId": product_id,
                "deviceName": d.get("deviceName"),
                "deviceStatus": device_status,
                "playToken": play_token,
                "channels": channels
            })
        return jsonify(devices), 200
    except requests.exceptions.RequestException as e:
        return jsonify({
            "error": "Erreur réseau Imou",
            "details": str(e)
        }), 500

@bp_camera.route('/alarm', methods=['POST', 'GET'])
def alarm():
    token_response = get_token()
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
            "deviceId": "4909BBDPSF5AED4",
            "channelId": 0,
            "count": 10,
            "beginTime": "2026-01-19 00:00:00",
            "endTime": "2026-01-20 23:59:59",
            "nextAlarmId": -1
        }
    }
    url = f"https://openapi-{DATACENTER}.easy4ip.com/openapi/getAlarmMessage"
    headers = {
        "Content-Type": "application/json"
    }
    try:
        response = requests.post(
            url,
            json=body,
            headers=headers,
            timeout=10
        )
        res_data = response.json()
        print(res_data)

        if res_data.get("result", {}).get("code") != "0":
            return jsonify({
                "error": "Erreur API Imou",
                "details": res_data.get("result", {}).get("msg"),
                "raw": res_data
            }), 400
        alarms = res_data["result"]["data"]["alarms"]
        TYPE_MAP = {
            "1": "MotionDetect",
            "2": "PIR",
            "3": "SoundDetect",
            "6": "HumanDetect",
            "10": "Intrusion",
            "11": "LineCross"
        }
        result = []
        for alarm in alarms:
            result.append({
                "alarmId": alarm.get("alarmId"),
                "type": TYPE_MAP.get(alarm.get("type"), "Unknown"),
                "labelType": alarm.get("labelType"),
                "time": alarm.get("localDate"),
                "image": (
                    alarm.get("picurlArray", [None])[0]
                    if alarm.get("picurlArray")
                    else alarm.get("thumbUrl")
                ),
                "video": None
            })
        return jsonify({"alarms": result})

    except requests.exceptions.RequestException as e:
        return jsonify({
            "error": "Erreur réseau",
            "details": str(e)
        }), 500

# MOVE CAMERA
@bp_camera.route('/ptz', methods=['POST'])
def ptz():
    data = request.json

    direction = data.get("direction")
    device_id = data.get("deviceId")
    channel_id = data.get("channelId", "0")
    token = data.get("token")

    operation_map = {
        "up": "0",
        "down": "1",
        "left": "2",
        "right": "3",
        "up_left": "4",
        "down_left": "5",
        "up_right": "6",
        "down_right": "7",
        "zoom_in": "8",
        "zoom_out": "9",
        "stop": "10"
    }

    operation = operation_map.get(direction)
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
            "deviceId":  device_id,
            "channelId": channel_id,
            "operation": operation,
            "duration": "300"
        }
    }

    url = f"https://openapi-{DATACENTER}.easy4ip.com/openapi/controlMovePTZ"
    r = requests.post(url, json=body, timeout=10)

    return jsonify(r.json())


















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




