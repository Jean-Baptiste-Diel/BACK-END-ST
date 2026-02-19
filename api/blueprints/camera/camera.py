from flask import Blueprint, jsonify, request, current_app
from api.utils.token import get_imou_token
from api.utils.utils_func import call_imou_api

camera_bp = Blueprint("camera", __name__)

# TOKEN
@camera_bp.route("/get-token", methods=["GET"])
def get_token_route():
    try:
        token, domain = get_imou_token()
        return jsonify({"accessToken": token, "currentDomain": domain}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

from flask import Blueprint, jsonify, current_app
from api.utils.token import get_imou_token
from api.utils.utils_func import call_imou_api

camera_bp = Blueprint("camera", __name__)

# LISTE DEVICES
@camera_bp.route("/devices", methods=["GET"])
def list_all_devices():
    try:
        page = 1
        page_size = 1
        all_devices = []

        while True:
            response_data = call_imou_api(
                "listDeviceDetailsByPage",
                {"page": page, "pageSize": page_size, "source": "bindAndShare"},
                timeout=10
            )

            # Vérification du code Imou
            if response_data.get("result", {}).get("code") != "0":
                return jsonify(response_data), 400

            device_list = response_data["result"]["data"].get("deviceList", [])
            if not device_list:
                break  # Plus de caméras à récupérer

            for d in device_list:
                channels_data = d.get("channels") or []

                channels = []
                if channels_data:
                    for c in channels_data:
                        channels.append({
                            "channelId": c.get("channelId", 0),
                            "channelName": c.get("channelName", "Main"),
                            "status": c.get("status", "unknown"),
                            "ptz": c.get("ptz") or False
                        })
                else:
                    # Si pas de canal, créer un canal principal par défaut
                    channels.append({
                        "channelId": 0,
                        "channelName": "Main",
                        "status": d.get("deviceStatus", "unknown"),
                        "ptz": "PTZ" in (d.get("deviceAbility") or "")
                    })

                all_devices.append({
                    "deviceId": d.get("deviceId"),
                    "deviceName": d.get("deviceName"),
                    "productId": d.get("productId"),
                    "deviceStatus": d.get("deviceStatus"),
                    "deviceModel": d.get("deviceModel"),
                    "deviceAbility": d.get("deviceAbility"),
                    "playToken": (d.get("playToken") or "").replace(" ", ""),
                    "channels": channels,
                    "upgradeInfo": d.get("upgradeInfo"),
                    "brand": d.get("brand")
                })

            # Si moins que page_size, c'est la dernière page
            if len(device_list) < page_size:
                break
            page += 1

        return jsonify(all_devices), 200

    except Exception as e:
        current_app.logger.exception(e)
        return jsonify({"error": "Erreur serveur"}), 500

# NIGHT VISION
@camera_bp.route("/camera-nightvision-info", methods=["GET"])
def camera_nightvision_info():
    device_id = request.args.get("deviceId")
    channel_id = request.args.get("channelId", "0")
    if not device_id:
        return jsonify({"error": "deviceId manquant"}), 400
    try:
        response_data = call_imou_api("getNightVisionMode", {"deviceId": device_id, "channelId": channel_id})
        return jsonify(response_data), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@camera_bp.route("/camera-nightvision", methods=["POST"])
def camera_nightvision():
    data = request.json
    device_id = data.get("deviceId")
    channel_id = data.get("channelId", "0")
    mode = data.get("mode")  # Infrared | Intelligent | FullColor | Off

    if not device_id or not mode:
        return jsonify({"error": "deviceId ou mode manquant"}), 400
    try:
        response_data = call_imou_api("setNightVisionMode", {
            "deviceId": device_id,
            "channelId": channel_id,
            "mode": mode
        })
        return jsonify(response_data), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# PTZ
@camera_bp.route("/ptz", methods=["POST"])
def ptz():
    data = request.json
    operation_map = {
        "up": "0", "down": "1", "left": "2", "right": "3",
        "up_left": "4", "down_left": "5", "up_right": "6", "down_right": "7",
        "zoom_in": "8", "zoom_out": "9", "stop": "10"
    }
    operation = operation_map.get(data.get("direction"))
    if not operation:
        return jsonify({"error": "Direction invalide"}), 400
    try:
        response_data = call_imou_api("controlMovePTZ", {
            "deviceId": data["deviceId"],
            "channelId": data.get("channelId", "0"),
            "operation": operation,
            "duration": "300"
        })
        return jsonify(response_data), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Récupérer l'état actuel de la caméra
@camera_bp.route("/camera/status", methods=["GET"])
def get_camera_status():
    device_id = request.args.get("deviceId")
    if not device_id:
        return jsonify({"error": "deviceId requis"}), 400

    try:
        response_data = call_imou_api("getDeviceCameraStatus", {"deviceId": device_id})

        if response_data.get("result", {}).get("code") != "0":
            return jsonify({
                "error": "Impossible de récupérer l'état de la caméra",
                "details": response_data
            }), 500

        enabled = response_data.get("result", {}).get("data", {}).get("enable", False)
        return jsonify({
            "deviceId": device_id,
            "enabled": enabled,
            "raw": response_data.get("result", {}).get("data")
        }), 200

    except Exception as e:
        current_app.logger.error(f"Erreur récupération état caméra : {e}")
        return jsonify({"error": str(e)}), 500

# Activer ou désactiver la caméra
@camera_bp.route("/camera/status", methods=["POST"])
def set_camera_status():
    """
    Etat de la variable enable : True = activer, False = désactiver
    """
    data = request.json
    device_id = data.get("deviceId")
    enable = data.get("enable", True)

    if not device_id:
        return jsonify({"error": "deviceId requis"}), 400

    try:
        response_data = call_imou_api("setDeviceCameraStatus", {
            "deviceId": device_id,
            "enable": enable
        })

        if response_data.get("result", {}).get("code") != "0":
            return jsonify({
                "error": "Impossible de modifier l'état de la caméra",
                "details": response_data
            }), 500

        return jsonify({
            "message": "État de la caméra mis à jour",
            "deviceId": device_id,
            "enabled": enable
        }), 200

    except Exception as e:
        current_app.logger.error(f"Erreur modification état caméra : {e}")
        return jsonify({"error": str(e)}), 500

