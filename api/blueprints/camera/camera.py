import time, uuid, hashlib, requests
from flask import Flask, jsonify, Blueprint, request

bp_camera = Blueprint("camera", __name__)

APP_ID = "lcea5699cd1d7c4457"
APP_SECRET = "f464f4b27e934bcba36125d953a4c6"

def sign(system):
    sign_str = f"appId{system['appId']}nonce{system['nonce']}time{system['time']}{APP_SECRET}"
    return hashlib.md5(sign_str.encode()).hexdigest()

@bp_camera.route("/api/imou/token", methods=["GET"])
def get_access_token():
    system = {
        "ver": "1.0",
        "appId": APP_ID,
        "time": int(time.time()),
        "nonce": str(uuid.uuid4())
    }
    system["sign"] = sign(system)

    payload = {
        "system": system,
        "id": str(uuid.uuid4()),
        "params": {}
    }

    url = "https://openapi-fk.easy4ip.com/openapi/accessToken"

    r = requests.post(url, json=payload, timeout=60)
    resp_json = r.json()
    print("IMOU ACCESS TOKEN RESPONSE:", resp_json)

    if resp_json.get("result", {}).get("code") == "0":
        return jsonify({
            "result": {
                "code": "0",
                "data": {
                    "accessToken": resp_json["result"]["data"]["accessToken"],
                    "expireTime": resp_json["result"]["data"]["expireTime"]
                }
            }
        })
    else:
        return jsonify({
            "result": {
                "code": "1",
                "msg": resp_json.get("result", {}).get("msg", "Erreur Imou")
            }
        }), 400


@bp_camera.route("/api/imou/live-stream", methods=["POST"])
def get_live_stream():
    data = request.json
    system = {
        "ver": "1.0",
        "appId": APP_ID,
        "time": int(time.time()),
        "nonce": str(uuid.uuid4())
    }
    system["sign"] = sign(system)

    payload = {
        "system": system,
        "id": str(uuid.uuid4()),
        "params": {
            "token": data["accessToken"],
            "deviceId": data["deviceId"],
            "channelId": data.get("channelId", "0"),
            "streamType": "hls"
        }
    }

    r = requests.post(
        "https://openapi-fk.easy4ip.com/openapi/lapp/liveStream/start",
        json=payload,
        timeout=10
    )

    resp_json = r.json()
    print("IMOU LIVE RESPONSE:", resp_json)

    if resp_json.get("result", {}).get("code") == "0":
        return jsonify({
            "result": {
                "code": "0",
                "data": {
                    "url": resp_json["result"]["data"]["url"]
                }
            }
        })
    else:
        return jsonify({
            "result": {
                "code": "1",
                "data": {},
                "msg": resp_json.get("result", {}).get("msg", "Erreur Imou")
            }
        })

