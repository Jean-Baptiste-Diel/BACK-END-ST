from datetime import datetime, timedelta
import requests
from flask import Blueprint, current_app, request, jsonify
from api.utils.utils_func import call_imou_api

alarme_bp = Blueprint("alarm", __name__)

# ROUTE POUR RÉCUPÉRER LES ALARMES
@alarme_bp.route('/alarm', methods=['POST'])
def alarm():
    """Récupère toutes les alarmes pour une caméra Imou sur 2 jours."""
    data = request.get_json(force=True)
    current_app.logger.info(f"Données reçues : {data}")

    device_id = data.get("deviceId")
    channel_id = str(data.get("channelId", "0"))

    if not device_id:
        return jsonify({"error": "deviceId manquant"}), 400

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

        current_app.logger.info(
            f"Alarme brute: alarmId={a.get('alarmId')}, type={type_alarme}, "
            f"labelType={a.get('labelType')}, pics={pics}, thumbUrl={a.get('thumbUrl')}, "
            f"videoUrl={a.get('videoUrl')}, time={a.get('localDate')}"
        )

        return {
            "alarmId": a.get("alarmId"),
            "type": type_alarme,
            "eventType": type_alarme,
            "time": a.get("localDate"),
            "image": image,
        }

    try:
        all_alarms = []
        next_alarm_id = "-1"
        count_per_call = 50

        while True:
            response_data = call_imou_api("getAlarmMessage", {
                "deviceId": device_id,
                "channelId": channel_id,
                "beginTime": begin_time,
                "endTime": end_time,
                "count": count_per_call,
                "nextAlarmId": next_alarm_id
            })

            current_app.logger.info(f"Données brutes API Imou : {response_data}")

            if response_data.get("result", {}).get("code") != "0":
                return jsonify({
                    "error": "Erreur API Imou",
                    "details": response_data.get("result", {}).get("msg"),
                    "raw": response_data
                }), 400

            alarms_brutes = response_data["result"]["data"].get("alarms", [])
            if not alarms_brutes:
                break

            all_alarms.extend([formater_alarme(a) for a in alarms_brutes])

            next_alarm_id = str(response_data["result"]["data"].get("nextAlarmId", "-1"))
            if next_alarm_id == "-1":
                break

        current_app.logger.info(f"Nombre total d'alarmes récupérées : {len(all_alarms)}")
        return jsonify({"count": len(all_alarms), "alarms": all_alarms}), 200

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

# RÉCUPÉRER LES VIDÉOS CLOUD
@alarme_bp.route("/camera/cloud/videos", methods=["GET"])
def get_cloud_videos():
    device_id = request.args.get("deviceId", "A449DAKPSFAAC72")
    channel_id = request.args.get("channelId", "0")
    count = int(request.args.get("count", 10))

    if not device_id:
        return jsonify({"error": "deviceId requis"}), 400

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
        response = call_imou_api("getCloudRecords", {
            "deviceId": device_id,
            "channelId": channel_id,
            "beginTime": begin_time,
            "endTime": end_time,
            "count": count
        })

        if response.get("result", {}).get("code") != "0":
            return jsonify({
                "error": "Erreur récupération vidéos cloud",
                "details": response
            }), 500

        records = response["result"]["data"].get("records", [])

        videos = []
        for r in records:
            videos.append({
                "recordId": r.get("recordId"),
                "beginTime": r.get("beginTime"),
                "endTime": r.get("endTime"),
                "duration": r.get("duration"),
                "thumbUrl": r.get("thumbUrl"),
                "videoUrl": r.get("playUrl")  # URL lecture directe
            })

        return jsonify({
            "deviceId": device_id,
            "count": len(videos),
            "videos": videos
        }), 200

    except Exception as e:
        current_app.logger.error(f"Erreur cloud videos : {e}")
        return jsonify({"error": str(e)}), 500

# LIRE UNE VIDÉO CLOUD PAR recordId
@alarme_bp.route("/camera/cloud/video/<record_id>", methods=["GET"])
def play_cloud_video(record_id):
    device_id = request.args.get("deviceId", "A449DAKPSFAAC72")
    channel_id = request.args.get("channelId", "0")

    try:
        response = call_imou_api("queryCloudRecords", {
            "deviceId": device_id,
            "channelId": channel_id,
            "beginTime": "2020-01-01 00:00:00",
            "endTime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "queryRange": "1-100"
        })

        if response.get("result", {}).get("code") != "0":
            return jsonify({"error": "Erreur API Imou"}), 500

        records = response["result"]["data"].get("records", [])

        for r in records:
            if r.get("recordId") == record_id:
                return jsonify({
                    "recordId": record_id,
                    "videoUrl": r.get("playUrl"),
                    "thumbUrl": r.get("thumbUrl"),
                    "beginTime": r.get("beginTime"),
                    "endTime": r.get("endTime")
                }), 200

        return jsonify({"error": "Vidéo non trouvée"}), 404

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# LIRE UNE VIDÉO DE LA CARTE SD
@alarme_bp.route("/camera/sd/video", methods=["GET"])
def play_sd_video():
    device_id = request.args.get("deviceId", "A449DAKPSFAAC72")
    channel_id = request.args.get("channelId", "0")

    if not device_id:
        return jsonify({"error": "deviceId requis"}), 400

    try:
        response = call_imou_api("playRecordFile", {
            "deviceId": device_id,
            "channelId": channel_id,
            "recordId": "1171990094824122400"
        })

        if response.get("result", {}).get("code") != "0":
            return jsonify({
                "error": "Erreur lecture vidéo SD",
                "details": response
            }), 500

        play_url = response["result"]["data"].get("playUrl")

        return jsonify({
            "recordId": "1171990094824122400",
            "videoUrl": play_url
        }), 200

    except Exception as e:
        current_app.logger.error(f"Erreur play SD video : {e}")
        return jsonify({"error": str(e)}), 500