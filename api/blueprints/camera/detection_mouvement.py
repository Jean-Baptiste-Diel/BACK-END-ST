from flask import Blueprint, request, jsonify, current_app
from api.utils.utils_func import call_imou_api

detection_bp = Blueprint("detection", __name__)

# Récupérer l'état de la détection
@detection_bp.route("/camera/motion-status", methods=["GET"])
def get_camera_motion_status():
    """
        device pour tester device_id = "A449DAKPSFE823B"
    """
    device_id = request.args.get("deviceId")
    channel_id = request.args.get("channelId", "0")

    if not device_id:
        return jsonify({"error": "deviceId requis"}), 400

    try:
        response_data = call_imou_api("getDeviceAlarmParam", {
            "deviceId": device_id,
            "channelId": channel_id
        })

        if response_data.get("result", {}).get("code") != "0":
            return jsonify({"error": "Impossible de récupérer le status", "details": response_data}), 500

        enable = response_data.get("result", {}).get("data", {}).get("enable", True)

        return jsonify({
            "deviceId": device_id,
            "channelId": channel_id,
            "enabled": enable,
            "raw": response_data["result"]["data"]
        })

    except Exception as e:
        current_app.logger.error(f"Erreur récupération motion: {e}")
        return jsonify({"error": str(e)}), 500

# Activer / désactiver la détection
@detection_bp.route("/camera/motion", methods=["POST"])
def set_camera_motion():
    data = request.json
    device_id = data.get("deviceId")
    channel_id = data.get("channelId", "0")
    enable = data.get("enable", True)

    if not device_id:
        return jsonify({"error": "deviceId requis"}), 400

    try:
        response_data = call_imou_api("modifyDeviceAlarmStatus", {
            "deviceId": device_id,
            "channelId": channel_id,
            "enable": enable
        })

        if response_data.get("result", {}).get("code") != "0":
            return jsonify({"error": "Impossible de changer le status", "details": response_data}), 500

        return jsonify({
            "message": "Détection mise à jour",
            "deviceId": device_id,
            "enabled": enable
        })

    except Exception as e:
        current_app.logger.error(f"Erreur modification motion: {e}")
        return jsonify({"error": str(e)}), 500

# Régler la sensibilité de la détection
@detection_bp.route("/camera/motion-sensitivity", methods=["POST"])
def set_camera_motion_sensitivity():
    data = request.json
    device_id = data.get("deviceId")
    channel_id = data.get("channelId", "0")
    sensitivity = data.get("sensitivity")

    if not device_id or sensitivity is None:
        return jsonify({"error": "deviceId et sensitivity requis"}), 400

    try:
        response_data = call_imou_api("setDeviceAlarmSensitivity", {
            "deviceId": device_id,
            "channelId": channel_id,
            "sensitivity": sensitivity
        })

        if response_data.get("result", {}).get("code") != "0":
            return jsonify({"error": "Impossible de changer la sensibilité", "details": response_data}), 500

        return jsonify({
            "message": "Sensibilité mise à jour",
            "deviceId": device_id,
            "channelId": channel_id,
            "sensitivity": sensitivity
        })

    except Exception as e:
        current_app.logger.error(f"Erreur modification sensibilité: {e}")
        return jsonify({"error": str(e)}), 500
