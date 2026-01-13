from flask import Flask, jsonify, request, Blueprint
import requests
import time



APP_ID = "lcea5699cd1d7c4457"
APP_SECRET = "f464f4b27e934bcba36125d953a4c6"
bd_c = Blueprint("c", __name__)
# Stockage simple du token en mémoire
access_token = None
token_expire_time = 0

def get_access_token():
    global access_token, token_expire_time
    if access_token and time.time() < token_expire_time:
        return access_token

    url = "https://openapi-fk.easy4ip.com/openapi/accessToken"
    payload = {"appKey": APP_ID, "appSecret": APP_SECRET}

    response = requests.post(url, json=payload)
    data = response.json()
    if response.status_code == 200 and "accessToken" in data:
        access_token = data["accessToken"]
        token_expire_time = time.time() + data["expireTime"] - 60
        return access_token
    else:
        print("Erreur token:", data)
        raise Exception(f"Impossible d'obtenir accessToken: {data}")


@bd_c.route("/devices", methods=["GET"])
def list_devices():
    token = get_access_token()
    url = "https://openapi.imoulife.com/v2/device/list"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return jsonify(response.json())
    else:
        return jsonify({"error": response.text}), response.status_code

@bd_c.route("/liveurl", methods=["GET"])
def get_live_url():
    token = get_access_token()
    device_serial = request.args.get("deviceSerial")
    if not device_serial:
        return jsonify({"error": "deviceSerial manquant"}), 400

    url = "https://openapi.imoulife.com/v2/device/liveurl"
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "deviceSerial": device_serial,
        "channelNo": 1,  # 1 = première caméra
        "streamType": 0,  # 0 = main stream
        "expireTime": 3600
    }
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 200:
        return jsonify(response.json())
    else:
        return jsonify({"error": response.text}), response.status_code

