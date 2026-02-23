from datetime import datetime, timedelta
import requests
from flask import Blueprint, current_app, request, jsonify
from api.utils.utils_func import call_imou_api

alarme_bp = Blueprint("alarm", __name__)

# ROUTE POUR RÉCUPÉRER LES ALARMES
@alarme_bp.route('/alarm', methods=['POST'])
def alarm():
    """Récupère les alarmes des 2 derniers jours pour une caméra Imou."""
    data = request.get_json(force=True)
    current_app.logger.info(f"Données reçues : {data}")

    device_id = "4909BBDPSF5AED4"#data.get("deviceId")
    channel_id = str(data.get("channelId", "0"))

    if not device_id:
        return jsonify({"error": "deviceId manquant"}), 400

    # Définir la période (2 derniers jours)
    now = datetime.now()
    begin_time = (now - timedelta(days=2)).strftime("%Y-%m-%d %H:%M:%S")
    end_time = now.strftime("%Y-%m-%d %H:%M:%S")
    current_app.logger.info(f"Période alarmes : {begin_time} → {end_time}")

    # Maps pour types d'alarmes
    alarm_type_map = {
        0: "HumanInfrared", 1: "Motion", 2: "Unknown", 3: "LowVoltage",
        4: "AccessoryHuman", 5: "SensorMovement", 6: "LongMovement",
        7: "AccessoryInfrared", 8: "DoorSensor", 90: "GatewayDoorSensor",
        91: "GatewayInfrared", 92: "GatewayLowBattery", 93: "GatewayTamper"
    }
    label_map = {"humanalarm": "Human", "vehiclealarm": "Vehicle", "animalalarm": "Animal"}

    def formater_alarme(a):
        """Formate une alarme pour l'API."""
        label_raw = (a.get("labelType") or "").lower()
        type_alarme = label_map.get(label_raw) or alarm_type_map.get(
            int(a.get("type", -1)), "Alarme inconnue"
        )
        image = ""
        pics = a.get("picurlArray")
        if isinstance(pics, list) and pics:
            image = pics[0]
        elif a.get("thumbUrl"):
            image = a.get("thumbUrl")

        return {
            "alarmId": a.get("alarmId"),
            "type": type_alarme,
            "eventType": type_alarme,
            "time": a.get("localDate"),
            "image": image,
            "video": a.get("videoUrl")
        }

    try:
        response_data = call_imou_api("getAlarmMessage", {
            "deviceId": device_id,
            "channelId": channel_id,
            "beginTime": begin_time,
            "endTime": end_time,
            "count": 30,
            "nextAlarmId": "-1"
        })

        if response_data.get("result", {}).get("code") != "0":
            return jsonify({
                "error": "Erreur API Imou",
                "details": response_data.get("result", {}).get("msg"),
                "raw": response_data
            }), 400

        alarms_brutes = response_data["result"]["data"].get("alarms", [])
        result = [formater_alarme(a) for a in alarms_brutes]
        current_app.logger.info(f"Alarme récupérée : {result}")

        return jsonify({"count": len(result), "alarms": result}), 200

    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"Erreur réseau Imou : {e}")
        return jsonify({"error": "Erreur réseau Imou", "details": str(e)}), 503

    except Exception as e:
        current_app.logger.error(f"Erreur serveur alarmes : {e}")
        return jsonify({"error": str(e)}), 500

# RÉCUPÉRER LES ALARMES SUR LA CARDSD
@alarme_bp.route("/camera/alarms", methods=["GET"])
def get_camera_alarms():
    device_id = "A449DAKPSFAAC72" #request.args.get("deviceId")
    channel_id = request.args.get("channelId", "0")
    count = int(request.args.get("count", 30))
    next_alarm_id = request.args.get("nextAlarmId", "-1")

    if not device_id:
        return jsonify({"error": "deviceId requis"}), 400

    # Par défaut : 2 derniers jours
    now = datetime.now()
    begin_time = request.args.get(
        "beginTime",
        (now - timedelta(days=2)).strftime("%Y-%m-%d %H:%M:%S")
    )
    end_time = request.args.get(
        "endTime",
        now.strftime("%Y-%m-%d %H:%M:%S")
    )

    try:
        response = call_imou_api("getAlarmMessage", {
            "deviceId": device_id,
            "channelId": channel_id,
            "beginTime": begin_time,
            "endTime": end_time,
            "count": count,
            "nextAlarmId": next_alarm_id
        })

        if response.get("result", {}).get("code") != "0":
            return jsonify({
                "error": "Erreur récupération alarmes",
                "details": response
            }), 500

        data = response["result"]["data"]
        alarms = data.get("alarms", [])

        return jsonify({
            "deviceId": device_id,
            "count": len(alarms),
            "nextAlarmId": data.get("nextAlarmId"),
            "alarms": alarms
        }), 200

    except Exception as e:
        current_app.logger.error(f"Erreur get alarms : {e}")
        return jsonify({"error": str(e)}), 500

# SUPPRIMER DES ALARMES SUR LA CARDSD
@alarme_bp.route("/camera/alarms/delete", methods=["POST"])
def delete_camera_alarms():
    data = request.json or {}
    device_id = data.get("deviceId")
    alarm_ids = data.get("alarmIds")

    if not device_id or not alarm_ids:
        return jsonify({
            "error": "deviceId et alarmIds requis"
        }), 400

    if not isinstance(alarm_ids, list):
        return jsonify({
            "error": "alarmIds doit être une liste"
        }), 400

    try:
        response = call_imou_api("deleteAlarmMessage", {
            "deviceId": device_id,
            "alarmIds": alarm_ids
        })

        if response.get("result", {}).get("code") != "0":
            return jsonify({
                "error": "Suppression échouée",
                "details": response
            }), 500

        return jsonify({
            "message": "Alarmes supprimées avec succès",
            "deletedCount": len(alarm_ids)
        }), 200

    except Exception as e:
        current_app.logger.error(f"Erreur delete alarms : {e}")
        return jsonify({"error": str(e)}), 500
