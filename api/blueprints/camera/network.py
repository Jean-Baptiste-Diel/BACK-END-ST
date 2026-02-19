from flask import jsonify, Blueprint, request

from api.utils.utils_func import call_imou_api

network_bp = Blueprint("network", __name__)

@network_bp.route("/camera/wifi", methods=["GET"])
def get_camera_wifi():
    #device_id = request.args.get("deviceId")
    device_id = "4909BBDPSF92B70"
    channel_id = request.args.get("channelId", "0")

    if not device_id:
        return jsonify({"error": "deviceId requis"}), 400

    try:
        response_data = call_imou_api("currentDeviceWifi", {
            "deviceId": device_id,
            "channelId": channel_id
        })

        if response_data.get("result", {}).get("code") != "0":
            return jsonify({"error": "Erreur Wi‑Fi", "details": response_data}), 500

        wifi_data = response_data["result"]["data"] or {}

        return jsonify({
            "deviceId": device_id,
            "wifi": {
              "ssid": wifi_data.get("ssid", ""),
              "rssi": wifi_data.get("rssi", ""),
              "status": wifi_data.get("linkStatus", "")
            }
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500
