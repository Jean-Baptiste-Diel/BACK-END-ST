from flask import Blueprint, request, jsonify, current_app
from api.utils.utils_func import call_imou_api

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

# Lister les enregistrements locaux
@storage_bp.route("/camera/records", methods=["GET"])
def get_local_records():
    device_id = request.args.get("deviceId")
    channel_id = request.args.get("channelId", "0") or "0"
    begin_time = request.args.get("beginTime")
    end_time = request.args.get("endTime")
    offset = int(request.args.get("offset", 0))
    limit = int(request.args.get("limit", 20))
    record_type = request.args.get("recordType", "0")

    if not all([device_id, begin_time, end_time]):
        return jsonify({"error": "deviceId, beginTime et endTime requis"}), 400

    try:
        response_data = call_imou_api("queryLocalRecords", {
            "deviceId": device_id,
            "channelId": channel_id,
            "beginTime": begin_time,
            "endTime": end_time,
            "offset": offset,
            "limit": limit,
            "recordType": record_type
        })

        result = response_data.get("result", {})
        code = result.get("code")
        records = result.get("data", {}).get("records", [])

        if code != "0":
            records = []

        formatted_records = [
            {
                "beginTime": r.get("beginTime"),
                "endTime": r.get("endTime"),
                "recordType": r.get("recordType"),
                "fileSize": r.get("fileSize"),
                "playUrl": r.get("playUrl")
            }
            for r in records
        ]

        return jsonify({
            "deviceId": device_id,
            "count": len(formatted_records),
            "records": formatted_records,
            "details": result if code != "0" else {}
        })

    except Exception as e:
        current_app.logger.exception(f"Erreur queryLocalRecords pour {device_id}: {e}")
        return jsonify({
            "deviceId": device_id,
            "count": 0,
            "records": []
        }), 200
