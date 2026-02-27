from flask import Blueprint, request, jsonify, current_app
from api.utils.utils_func import call_imou_api

operate_bp = Blueprint("operate", __name__)

erreur_deviceId = "deviceId requis"

# SNAPSHOT AMÉLIORÉ
@operate_bp.route("/camera/snap-hd", methods=["POST"])
def set_device_snap_enhanced():
    data = request.json
    device_id = data.get("deviceId")
    channel_id = data.get("channelId", "1")

    if not device_id:
        return jsonify({"error": erreur_deviceId}), 400

    try:
        res = call_imou_api("setDeviceSnapEnhanced", {
            "deviceId": device_id,
            "channelId": channel_id
        })
        return jsonify(res)
    except Exception as e:
        current_app.logger.error(f"Snap HD error: {e}")
        return jsonify({"error": str(e)}), 500

# PTZ – MOUVEMENT
@operate_bp.route("/camera/ptz/move", methods=["POST"])
def ptz_move():
    data = request.json

    required = ["deviceId", "operation"]
    if not all(k in data for k in required):
        return jsonify({"error": "deviceId et operation requis"}), 400

    try:
        res = call_imou_api("controlMovePTZ", {
            "deviceId": data["deviceId"],
            "channelId": data.get("channelId", "0"),
            "operation": data["operation"],
            "duration": data.get("duration", "300")
        })
        return jsonify(res)
    except Exception as e:
        current_app.logger.error(f"PTZ move error: {e}")
        return jsonify({"error": str(e)}), 500

# PTZ – ALLER À UNE POSITION
@operate_bp.route("/camera/ptz/location", methods=["POST"])
def ptz_location():
    data = request.json

    if not data.get("deviceId"):
        return jsonify({"error": erreur_deviceId}), 400

    try:
        res = call_imou_api("controlLocationPTZ", {
            "deviceId": data["deviceId"],
            "channelId": data.get("channelId", "0"),
            "position": data.get("position")
        })
        return jsonify(res)
    except Exception as e:
        current_app.logger.error(f"PTZ location error: {e}")
        return jsonify({"error": str(e)}), 500

# INFOS PTZ
@operate_bp.route("/camera/ptz/info", methods=["GET"])
def ptz_info():
    device_id = request.args.get("deviceId")
    channel_id = request.args.get("channelId", "0")

    if not device_id:
        return jsonify({"error": erreur_deviceId}), 400

    try:
        res = call_imou_api("devicePTZInfo", {
            "deviceId": device_id,
            "channelId": channel_id
        })
        return jsonify(res)
    except Exception as e:
        current_app.logger.error(f"PTZ info error: {e}")
        return jsonify({"error": str(e)}), 500

# REDÉMARRER LA CAMÉRA
@operate_bp.route("/camera/restart", methods=["POST"])
def restart_camera():
    data = request.json
    device_id = data.get("deviceId")

    if not device_id:
        return jsonify({"error": erreur_deviceId}), 400

    try:
        res = call_imou_api("restartDevice", {
            "deviceId": device_id
        })
        return jsonify(res)
    except Exception as e:
        current_app.logger.error(f"Restart error: {e}")
        return jsonify({"error": str(e)}), 500

# SYNCHRONISER L’HEURE
@operate_bp.route("/camera/time/sync", methods=["POST"])
def sync_camera_time():
    data = request.json
    device_id = data.get("deviceId")

    if not device_id:
        return jsonify({"error": erreur_deviceId}), 400

    try:
        res = call_imou_api("calibrationDeviceTime", {
            "deviceId": device_id
        })
        return jsonify(res)
    except Exception as e:
        current_app.logger.error(f"Time sync error: {e}")
        return jsonify({"error": str(e)}), 500

# RÉCUPÉRER L’HEURE DE LA CAMÉRA
@operate_bp.route("/camera/time", methods=["GET"])
def get_camera_time():
    device_id = request.args.get("deviceId")
    if not device_id:
        return jsonify({"error": erreur_deviceId}), 400

    try:
        res = call_imou_api("getDeviceTime", {
            "deviceId": device_id
        })
        return jsonify(res)
    except Exception as e:
        current_app.logger.error(f"Get time error: {e}")
        return jsonify({"error": str(e)}), 500
