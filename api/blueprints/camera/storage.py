from flask import Blueprint, request, jsonify, current_app, json
from api.utils.utils_func import call_imou_api
from datetime import datetime, timedelta

storage_bp = Blueprint("storage", __name__)

erreur_deviceId = "deviceId requis"

# Vérifier l'état de la carte SD
@storage_bp.route("/camera/sdcard-status", methods=["GET"])
def get_sdcard_status():
    device_id = request.args.get("deviceId")
    channel_id = request.args.get("channelId", "0") or "0"

    if not device_id:
        return jsonify({"error": erreur_deviceId}), 400

    try:
        response_data = call_imou_api("deviceSdcardStatus", {
            "deviceId": device_id,
            "channelId": channel_id
        })

        result = response_data.get("result", {})
        code = result.get("code")
        data = result.get("data", {})

        # Si code différent de 0 → device sleeping/offline
        if code != "0":
            sd_status = {"status": "sleep" if code == "DV1030" else "unknown"}
            return jsonify({
                "deviceId": device_id,
                "channelId": channel_id,
                "sdcardStatus": sd_status,
                "details": result
            }), 200

        return jsonify({
            "deviceId": device_id,
            "channelId": channel_id,
            "sdcardStatus": data
        })

    except Exception as e:
        current_app.logger.exception(f"Erreur récupération SD pour {device_id}: {e}")
        return jsonify({
            "deviceId": device_id,
            "channelId": channel_id,
            "sdcardStatus": {"status": "unknown"}
        }), 200

# Obtenir les informations de stockage
@storage_bp.route("/camera/storage-info", methods=["GET"])
def get_storage_info():
    device_id = request.args.get("deviceId")
    channel_id = request.args.get("channelId", "0") or "0"

    if not device_id:
        return jsonify({"error": erreur_deviceId}), 400

    try:
        response_data = call_imou_api("deviceStorage", {
            "deviceId": device_id,
            "channelId": channel_id
        })

        result = response_data.get("result", {})
        code = result.get("code")
        data = result.get("data", {})

        if code != "0":
            storage_info = {"status": "unknown"}
            return jsonify({
                "deviceId": device_id,
                "channelId": channel_id,
                "storageInfo": storage_info,
                "details": result
            }), 200

        return jsonify({
            "deviceId": device_id,
            "channelId": channel_id,
            "storageInfo": data
        })

    except Exception as e:
        current_app.logger.exception(f"Erreur récupération stockage pour {device_id}: {e}")
        return jsonify({
            "deviceId": device_id,
            "channelId": channel_id,
            "storageInfo": {"status": "unknown"}
        }), 200

# Récupérer / formater la carte SD
@storage_bp.route("/camera/recover-sdcard", methods=["POST"])
def recover_sdcard():
    data = request.json or {}
    device_id = data.get("deviceId")
    channel_id = data.get("channelId", "0") or "0"

    if not device_id:
        return jsonify({"error": erreur_deviceId}), 400

    try:
        response_data = call_imou_api("recoverSDCard", {
            "deviceId": device_id,
            "channelId": channel_id
        })

        result = response_data.get("result", {})
        code = result.get("code")

        if code != "0":
            return jsonify({
                "deviceId": device_id,
                "channelId": channel_id,
                "message": "Impossible de récupérer/formater la SD",
                "details": result
            }), 200

        return jsonify({
            "deviceId": device_id,
            "channelId": channel_id,
            "message": "Carte SD récupérée / formatée avec succès"
        })

    except Exception as e:
        current_app.logger.exception(f"Erreur récupération SD pour {device_id}: {e}")
        return jsonify({
            "deviceId": device_id,
            "channelId": channel_id,
            "message": "Erreur serveur",
            "sdcardStatus": {"status": "unknown"}
        }), 200

# Compter les enregistrements locaux
@storage_bp.route("/camera/records/count", methods=["GET"])
def get_local_record_count():
    device_id = request.args.get("deviceId")
    channel_id = request.args.get("channelId", "0") or "0"
    begin_time = request.args.get("beginTime")
    end_time = request.args.get("endTime")
    record_type = request.args.get("recordType", "0")

    if not all([device_id, begin_time, end_time]):
        return jsonify({"error": "deviceId, beginTime et endTime requis"}), 400

    try:
        response_data = call_imou_api("queryLocalRecordNum", {
            "deviceId": device_id,
            "channelId": channel_id,
            "beginTime": begin_time,
            "endTime": end_time,
            "recordType": record_type
        })

        result = response_data.get("result", {})
        code = result.get("code")
        total = result.get("data", {}).get("total", 0)

        if code != "0":
            total = 0

        return jsonify({
            "deviceId": device_id,
            "totalRecords": total,
            "details": result if code != "0" else {}
        })

    except Exception as e:
        current_app.logger.exception(f"Erreur queryLocalRecordNum pour {device_id}: {e}")
        return jsonify({
            "deviceId": device_id,
            "totalRecords": 0
        }), 200

# Lister les enregistrements locaux ok
@storage_bp.route("/camera/records", methods=["GET"])
def get_local_records():
    device_id = "4909BBDPSF5AED4"   #request.args.get("deviceId")
    channel_id = request.args.get("channelId", "0") or "0"

    if not device_id:
        return jsonify({"error": "deviceId requis"}), 400

    try:
        end_time = datetime.utcnow()
        begin_time = end_time - timedelta(days=2)

        begin_time_str = begin_time.strftime("%Y-%m-%d %H:%M:%S")
        end_time_str = end_time.strftime("%Y-%m-%d %H:%M:%S")

        offset = 0
        limit = 50
        all_records = []

        while True:
            response_data = call_imou_api("queryLocalRecords", {
                "deviceId": device_id,
                "channelId": channel_id,
                "beginTime": begin_time_str,
                "endTime": end_time_str,
                "offset": offset,
                "limit": limit,
                "recordType": "0"
            })

            result = response_data.get("result", {})
            code = result.get("code")

            if code != "0":
                break

            records = result.get("data", {}).get("records", [])

            if not records:
                break

            all_records.extend(records)

            if len(records) < limit:
                break

            offset += limit

        formatted_records = [
            {
                "recordId": r.get("recordId"),
                "beginTime": r.get("beginTime"),
                "endTime": r.get("endTime"),
                "type": r.get("type"),
                "fileLength": r.get("fileLength"),
                "channelId": r.get("channelID")
            }
            for r in all_records
        ]

        return jsonify({
            "deviceId": device_id,
            "count": len(formatted_records),
            "records": formatted_records,
            "period": {
                "beginTime": begin_time_str,
                "endTime": end_time_str
            }
        })

    except Exception as e:
        current_app.logger.exception(f"Erreur queryLocalRecords pour {device_id}: {e}")
        return jsonify({
            "deviceId": device_id,
            "count": 0,
            "records": []
        }), 200

# Récupérer les enregistrements cloud (2 derniers jours)
@storage_bp.route("/camera/cloud-records", methods=["GET"])
def get_cloud_records():
    device_id = "4909BBDPSFC73D9"  # request.args.get("deviceId")
    channel_id = request.args.get("channelId", "0") or "0"

    if not device_id:
        return jsonify({"error": "deviceId requis"}), 400

    try:
        end_time = datetime.utcnow()
        begin_time = end_time - timedelta(days=2)

        begin_time_str = begin_time.strftime("%Y-%m-%d %H:%M:%S")
        end_time_str = end_time.strftime("%Y-%m-%d %H:%M:%S")

        all_records = []
        next_token = None

        # --- Récupération des cloud records ---
        while True:
            payload = {
                "deviceId": device_id,
                "channelId": channel_id,
                "beginTime": begin_time_str,
                "endTime": end_time_str,
                "count": 30
            }
            if next_token:
                payload["nextToken"] = next_token

            response_data = call_imou_api("getCloudRecords", payload)
            result = response_data.get("result", {})
            code = result.get("code")
            if code != "0":
                break

            data = result.get("data", {})
            records = data.get("records", [])
            if not records:
                break

            all_records.extend(records)
            next_token = data.get("nextToken")
            if not next_token:
                break

        # --- Récupération des alarmes pour avoir thumbnails/images ---
        all_alarms = []
        next_alarm_id = None

        while True:
            alarm_payload = {
                "deviceId": device_id,
                "channelId": channel_id,
                "beginTime": begin_time_str,
                "endTime": end_time_str,
                "count": 30
            }
            if next_alarm_id:
                alarm_payload["nextAlarmId"] = next_alarm_id

            alarm_response = call_imou_api("getAlarmMessage", alarm_payload)
            alarm_result = alarm_response.get("result", {})
            if alarm_result.get("code") != "0":
                break

            alarm_data = alarm_result.get("data", {})
            alarms = alarm_data.get("alarms", [])
            if not alarms:
                break

            all_alarms.extend(alarms)
            next_alarm_id = alarm_data.get("nextAlarmId")
            if not next_alarm_id:
                break

        # --- Fusion des données ---
        formatted_records = []

        for r in all_records:
            # On cherche si on a une alarme correspondante pour avoir images/thumbnails
            alarm_match = next((a for a in all_alarms if a.get("beginTime") == r.get("beginTime")), {})
            formatted_records.append({
                "beginTime": r.get("beginTime"),
                "endTime": r.get("endTime"),
                "type": r.get("type"),
                "fileSize": r.get("fileSize"),
                "thumbnail": alarm_match.get("thumbUrl"),
                "images": alarm_match.get("picurlArray", []),
                "alarmType": alarm_match.get("type")
            })

        return jsonify({
            "deviceId": device_id,
            "count": len(formatted_records),
            "records": formatted_records,
            "period": {
                "beginTime": begin_time_str,
                "endTime": end_time_str
            }
        })

    except Exception as e:
        current_app.logger.exception(f"Erreur getCloudRecords pour {device_id}: {e}")
        return jsonify({
            "deviceId": device_id,
            "count": 0,
            "records": []
        }), 200

# Récupérer les alertes caméra (2 derniers jours)
@storage_bp.route("/camera/alarms", methods=["GET"])
def get_camera_alarms():
    device_id = "A449DAKPSFAAC72" #request.args.get("deviceId")
    channel_id = request.args.get("channelId", "0") or "0"

    if not device_id:
        return jsonify({"error": "deviceId requis"}), 400

    try:
        # période : 2 derniers jours
        end_time = datetime.utcnow()
        begin_time = end_time - timedelta(days=2)

        begin_time_str = begin_time.strftime("%Y-%m-%d %H:%M:%S")
        end_time_str = end_time.strftime("%Y-%m-%d %H:%M:%S")

        next_alarm_id = None
        all_alarms = []

        while True:
            payload = {
                "deviceId": device_id,
                "channelId": channel_id,
                "beginTime": begin_time_str,
                "endTime": end_time_str,
                "count": 30
            }

            if next_alarm_id:
                payload["nextAlarmId"] = next_alarm_id

            response_data = call_imou_api("getAlarmMessage", payload)

            result = response_data.get("result", {})
            code = result.get("code")

            if code != "0":
                break

            data = result.get("data", {})
            alarms = data.get("alarms", [])

            if not alarms:
                break

            all_alarms.extend(alarms)

            next_alarm_id = data.get("nextAlarmId")

            if not next_alarm_id:
                break

        formatted_alarms = [
            {
                "alarmId": a.get("alarmId"),
                "time": a.get("localDate"),
                "type": a.get("type"),
                "thumbnail": a.get("thumbUrl"),
                "images": a.get("picurlArray", [])
            }
            for a in all_alarms
        ]

        return jsonify({
            "deviceId": device_id,
            "count": len(formatted_alarms),
            "alarms": formatted_alarms,
            "period": {
                "beginTime": begin_time_str,
                "endTime": end_time_str
            }
        })

    except Exception as e:
        current_app.logger.exception(f"Erreur getAlarmMessage pour {device_id}: {e}")
        return jsonify({
            "deviceId": device_id,
            "count": 0,
            "alarms": []
        }), 200

@storage_bp.route("/camera/query-cloud-records", methods=["GET"])
def query_cloud_records():
    device_id = "A449DAKPSFAAC72" #request.args.get("deviceId")
    channel_id = request.args.get("channelId", "0") or "0"

    if not device_id:
        return jsonify({"error": "deviceId requis"}), 400

    try:
        # période : derniers 30 jours
        end_time = datetime.utcnow()
        begin_time = end_time - timedelta(days=30)

        begin_time_str = begin_time.strftime("%Y-%m-%d %H:%M:%S")
        end_time_str = end_time.strftime("%Y-%m-%d %H:%M:%S")

        all_records = []
        current_begin = begin_time_str

        while True:
            payload = {
                "deviceId": device_id,
                "channelId": channel_id,
                "beginTime": current_begin,
                "endTime": end_time_str,
                "queryRange": "1-100"  # demande jusqu'à 100 vidéos à chaque appel
            }

            response_data = call_imou_api("queryCloudRecords", payload)
            result = response_data.get("result", {})

            # vérifie si ok
            if result.get("code") != "0":
                break

            data = result.get("data", {})
            records = data.get("records", [])

            if not records:
                break

            all_records.extend(records)

            # suivante : on prend le plus grand endTime comme nouveau beginTime
            last_end_time = records[-1].get("endTime")
            if not last_end_time or last_end_time == current_begin:
                break

            current_begin = last_end_time

        # formater les résultats
        formatted = [
            {
                "recordId": r.get("recordId"),
                "beginTime": r.get("beginTime"),
                "endTime": r.get("endTime"),
                "thumbUrl": r.get("thumbUrl"),
                "size": r.get("size"),
                "recordRegionId": r.get("recordRegionId")
            }
            for r in all_records
        ]

        return jsonify({
            "deviceId": device_id,
            "count": len(formatted),
            "records": formatted,
            "period": {
                "beginTime": begin_time_str,
                "endTime": end_time_str
            }
        })

    except Exception as e:
        current_app.logger.exception(f"Erreur queryCloudRecords pour {device_id}: {e}")
        return jsonify({"error": "Erreur serveur"}), 500