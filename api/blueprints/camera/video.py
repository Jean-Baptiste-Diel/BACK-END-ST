from flask import Blueprint, request, jsonify, current_app
from api.utils.utils_func import call_imou_api

video_bp = Blueprint("video", __name__)

erreur_deviceId = "deviceId requis"

# Récupérer le zoom actuel
"""
    @video_bp.route("/camera/zoom-status", methods=["GET"])
    def get_camera_zoom():
        device_id = '4909BBDPSF5AED4'#request.args.get("deviceId")
        channel_id = request.args.get("channelId", "0")
        if not device_id:
            return jsonify({"error": erreur_deviceId}), 400
        try:
            response_data = call_imou_api("getZoomFocus", {"deviceId": device_id, "channelId": channel_id})
            if response_data.get("result", {}).get("code") != "0":
                return jsonify({"error": "Impossible de récupérer le zoom", "details": response_data}), 500
            zoom = response_data.get("result", {}).get("data", {}).get("channels", [{}])[0].get("zoomFocus", 0)
            return jsonify({"deviceId": device_id, "channelId": channel_id, "zoomFocus": zoom})
        except Exception as e:
            current_app.logger.error(f"Erreur récupération zoom: {e}")
            return jsonify({"error": str(e)}), 500
"""
# Définir le zoom
"""
    @video_bp.route("/camera/zoom", methods=["POST"])
    def set_camera_zoom():
        data = request.json
        device_id = data.get("deviceId")
        channel_id = data.get("channelId", "0")
        zoom_type = data.get("type")  # "large", "small", "cover"
        zoom_focus = data.get("zoomFocus")  # entre "0.0" et "1.0"
    
        if not device_id or not zoom_type or zoom_focus is None:
            return jsonify({"error": "deviceId, type et zoomFocus requis"}), 400
        try:
            response_data = call_imou_api("setZoomFocus", {
                "deviceId": device_id,
                "channelId": channel_id,
                "type": zoom_type,
                "zoomFocus": zoom_focus
            })
            if response_data.get("result", {}).get("code") != "0":
                return jsonify({"error": "Impossible de modifier le zoom", "details": response_data}), 500
            return jsonify({"message": "Zoom mis à jour", "deviceId": device_id, "zoomFocus": zoom_focus})
        except Exception as e:
            current_app.logger.error(f"Erreur modification zoom: {e}")
            return jsonify({"error": str(e)}), 500
"""
# Récupérer le mode nuit actuel
@video_bp.route("/camera/nightvision-status", methods=["GET"])
def get_camera_nightvision():
    device_id = 'A449DAKPSFAAC72'#request.args.get("deviceId")
    channel_id = request.args.get("channelId", "0")
    if not device_id:
        return jsonify({"error": erreur_deviceId}), 400
    try:
        response_data = call_imou_api("getNightVisionMode", {"deviceId": device_id, "channelId": channel_id})
        if response_data.get("result", {}).get("code") != "0":
            return jsonify({"error": "Impossible de récupérer le mode nuit", "details": response_data}), 500
        mode = response_data.get("result", {}).get("data", {}).get("mode", "Unknown")
        return jsonify({"deviceId": device_id, "channelId": channel_id, "mode": mode})
    except Exception as e:
        current_app.logger.error(f"Erreur récupération mode nuit: {e}")
        return jsonify({"error": str(e)}), 500

# Définir le mode nuit
@video_bp.route("/camera/nightvision", methods=["POST"])
def set_camera_nightvision():
    data = request.json
    device_id = 'A449DAKPSFAAC72'#data.get("deviceId")
    channel_id = data.get("channelId","0")
    mode = data.get("mode")  # Infrared | FullColor | Intelligent | Off

    if not device_id or not mode:
        return jsonify({"error": "deviceId et mode requis"}), 400
    try:
        response_data = call_imou_api("setNightVisionMode", {
            "deviceId": device_id,
            "channelId": channel_id,
            "mode": mode
        })
        if response_data.get("result", {}).get("code") != "0":
            return jsonify({"error": "Impossible de modifier le mode nuit", "details": response_data}), 500
        return jsonify({"message": "Mode nuit mis à jour", "deviceId": device_id, "mode": mode})
    except Exception as e:
        current_app.logger.error(f"Erreur modification mode nuit: {e}")
        return jsonify({"error": str(e)}), 500

# Récupérer la sensibilité du fill light
"""
    @video_bp.route("/camera/filllight-status", methods=["GET"])
    def get_camera_filllight():
        device_id = '4909BBDPSF5AED4'#data.get("deviceId")
        channel_id = request.args.get("channelId", "0")
        if not device_id:
            return jsonify({"error": erreur_deviceId}), 400
        try:
            response_data = call_imou_api("getFillLightSensitivity", {"deviceId": device_id, "channelId": channel_id})
            if response_data.get("result", {}).get("code") != "0":
                return jsonify({"error": "Impossible de récupérer la sensibilité", "details": response_data}), 500
            sensitivity = response_data.get("result", {}).get("data", {}).get("sensitivity", "1")
            return jsonify({"deviceId": device_id, "channelId": channel_id, "sensitivity": sensitivity})
        except Exception as e:
            current_app.logger.error(f"Erreur récupération fill light: {e}")
            return jsonify({"error": str(e)}), 500
"""

# Définir la sensibilité du fill light
"""
    @video_bp.route("/camera/filllight", methods=["POST"])
    def set_camera_filllight():
        data = request.json
        device_id = data.get("deviceId")
        channel_id = data.get("channelId", "0")
        sensitivity = data.get("sensitivity")
    
        if not device_id or sensitivity is None:
            return jsonify({"error": "deviceId et sensitivity requis"}), 400
        try:
            response_data = call_imou_api("setFillLightSensitivity", {
                "deviceId": device_id,
                "channelId": channel_id,
                "sensitivity": sensitivity
            })
            if response_data.get("result", {}).get("code") != "0":
                return jsonify({"error": "Impossible de modifier la sensibilité", "details": response_data}), 500
            return jsonify(
                {"message": "Sensibilité fill light mise à jour", "deviceId": device_id, "sensitivity": sensitivity})
        except Exception as e:
            current_app.logger.error(f"Erreur modification fill light: {e}")
            return jsonify({"error": str(e)}), 500
"""