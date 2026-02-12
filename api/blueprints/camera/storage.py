from flask import Blueprint, request, jsonify, current_app
from api.utils.utils_func import call_imou_api

storage_bp = Blueprint("storage", __name__)

erreur_deviceId = "deviceId requis"
# Vérifier l'état de la carte SD
@storage_bp.route("/camera/sdcard-status", methods=["GET"])
def get_sdcard_status():
    """
    device pour tester device_id = "A449DAKPSFE823B"
    """
    device_id = request.args.get("deviceId")
    channel_id = request.args.get("channelId", "0")

    if not device_id:
        return jsonify({"error": erreur_deviceId}), 400

    try:
        response_data = call_imou_api("deviceSdcardStatus", {
            "deviceId": device_id,
            "channelId": channel_id
        })

        if response_data.get("result", {}).get("code") != "0":
            return jsonify({"error": "Impossible de récupérer le status SD", "details": response_data}), 500

        sd_status = response_data.get("result", {}).get("data", {})
        return jsonify({
            "deviceId": device_id,
            "channelId": channel_id,
            "sdcardStatus": sd_status
        })

    except Exception as e:
        current_app.logger.error(f"Erreur récupération SD: {e}")
        return jsonify({"error": str(e)}), 500

# Obtenir les informations de stockage
@storage_bp.route("/camera/storage-info", methods=["GET"])
def get_storage_info():
    device_id = request.args.get("deviceId")
    channel_id = request.args.get("channelId", "0")

    if not device_id:
        return jsonify({"error": erreur_deviceId}), 400

    try:
        response_data = call_imou_api("deviceStorage", {
            "deviceId": device_id,
            "channelId": channel_id
        })

        if response_data.get("result", {}).get("code") != "0":
            return jsonify({"error": "Impossible de récupérer le stockage", "details": response_data}), 500

        storage_info = response_data.get("result", {}).get("data", {})
        return jsonify({
            "deviceId": device_id,
            "channelId": channel_id,
            "storageInfo": storage_info
        })

    except Exception as e:
        current_app.logger.error(f"Erreur récupération stockage: {e}")
        return jsonify({"error": str(e)}), 500

# Récupérer / formater la carte SD
@storage_bp.route("/camera/recover-sdcard", methods=["POST"])
def recover_sdcard():
    data = request.json
    device_id = data.get("deviceId")
    channel_id = data.get("channelId", "0")

    if not device_id:
        return jsonify({"error": erreur_deviceId}), 400

    try:
        response_data = call_imou_api("recoverSDCard", {
            "deviceId": device_id,
            "channelId": channel_id
        })

        if response_data.get("result", {}).get("code") != "0":
            return jsonify({"error": "Impossible de récupérer/formater la SD", "details": response_data}), 500

        return jsonify({
            "message": "Carte SD récupérée / formatée avec succès",
            "deviceId": device_id,
            "channelId": channel_id
        })

    except Exception as e:
        current_app.logger.error(f"Erreur récupération SD: {e}")
        return jsonify({"error": str(e)}), 500

@storage_bp.route("/camera/records/count", methods=["GET"])
def get_local_record_count():
    device_id = request.args.get("deviceId")
    channel_id = request.args.get("channelId", "0")
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

        if response_data.get("result", {}).get("code") != "0":
            return jsonify({
                "error": "Impossible de récupérer le nombre d'enregistrements",
                "details": response_data
            }), 500

        total = response_data["result"]["data"].get("total", 0)

        return jsonify({
            "deviceId": device_id,
            "totalRecords": total
        })

    except Exception as e:
        current_app.logger.error(f"Erreur queryLocalRecordNum: {e}")
        return jsonify({"error": str(e)}), 500

@storage_bp.route("/camera/records", methods=["GET"])
def get_local_records():
    device_id = request.args.get("deviceId")
    channel_id = request.args.get("channelId", "0")
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

        if response_data.get("result", {}).get("code") != "0":
            return jsonify({
                "error": "Impossible de récupérer les vidéos",
                "details": response_data
            }), 500

        records = response_data["result"]["data"].get("records", [])

        formatted_records = []
        for r in records:
            formatted_records.append({
                "beginTime": r.get("beginTime"),
                "endTime": r.get("endTime"),
                "recordType": r.get("recordType"),
                "fileSize": r.get("fileSize"),
                "playUrl": r.get("playUrl")
            })

        return jsonify({
            "deviceId": device_id,
            "count": len(formatted_records),
            "records": formatted_records
        })

    except Exception as e:
        current_app.logger.error(f"Erreur queryLocalRecords: {e}")
        return jsonify({"error": str(e)}), 500
