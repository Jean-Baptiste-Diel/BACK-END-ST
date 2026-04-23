from flask import Blueprint, jsonify
from pip._internal import req

from api.crud.crud_pompe.pompe import get_devices
from api.utils.token import get_tuya_token
from api.utils.utils_func import call_tuya_api

pompe_bp = Blueprint("pompe_bp", __name__)

# GET DEVICES ROUTE
@pompe_bp.route("/devices/pompes", methods=["GET"])
def devices_route():
    token_response = get_tuya_token()
    if not token_response.get("success"):
        return jsonify(token_response), 400
    access_token = token_response["result"]["access_token"]
    devices = get_devices(access_token)
    return jsonify(devices)


# Ouvre la pompe immediatement
@pompe_bp.route("/device/<device_id>/issue", methods=["POST"])
def issue_command(device_id):

    # 1. TOKEN
    token_response = get_tuya_token()

    if not token_response.get("success"):
        return jsonify(token_response), 400

    access_token = token_response["result"]["access_token"]

    # 2. INPUT FRONT
    data = req.json
    switch_value = data.get("switch_1", True)

    # 3. BODY TUYA
    body = {
        "properties": f'{{"switch_1": {str(switch_value).lower()}}}'
    }

    # 4. API CALL
    path = f"/v2.0/cloud/thing/{device_id}/shadow/properties/issue"

    res = call_tuya_api(
        method="POST",
        path=path,
        access_token=access_token,
        body=body
    )

    return jsonify(res)

# Ouvrir la pompe lorsqu'il sera en ligne
@pompe_bp.route("/device/<device_id>/desired", methods=["POST"])
def set_desired(device_id):

    # 1. TOKEN
    token_response = get_tuya_token()

    if not token_response.get("success"):
        return jsonify(token_response), 400

    access_token = token_response["result"]["access_token"]

    # 2. DATA FRONT
    data = req.json

    switch_value = data.get("switch_1", True)
    duration = data.get("duration", 1000)

    # 3. BODY TUYA
    body = {
        "properties": f'{{"switch_1": {str(switch_value).lower()}}}',
        "duration": duration,
        "type": 1
    }

    # 4. CALL TUYA API
    path = f"/v2.0/cloud/thing/{device_id}/shadow/properties/desired"

    res = call_tuya_api(
        method="POST",
        path=path,
        access_token=access_token,
        body=body
    )

    return jsonify(res)

# Capaciter d'une pompe
@pompe_bp.route("/device/<device_id>/model", methods=["GET"])
def get_model(device_id):

    # 1. TOKEN
    token_response = get_tuya_token()

    if not token_response.get("success"):
        return jsonify(token_response), 400

    access_token = token_response["result"]["access_token"]

    # 2. API CALL
    path = f"/v2.0/cloud/thing/{device_id}/model"

    res = call_tuya_api(
        method="GET",
        path=path,
        access_token=access_token
    )

    return jsonify(res)

# Logs et historique
@pompe_bp.route("/device/<device_id>/desired", methods=["GET"])
def get_desired(device_id):

    # 1. TOKEN
    token_response = get_tuya_token()

    if not token_response.get("success"):
        return jsonify(token_response), 400

    access_token = token_response["result"]["access_token"]

    # 2. API PATH
    path = f"/v2.0/cloud/thing/{device_id}/shadow/properties/desired"

    # 3. CALL TUYA
    res = call_tuya_api(
        method="GET",
        path=path,
        access_token=access_token
    )

    return jsonify(res)

# renommer les switchs
@pompe_bp.route("/device/<device_id>/rename", methods=["POST"])
def rename_property(device_id):

    token_response = get_tuya_token()

    if not token_response.get("success"):
        return jsonify(token_response), 400

    access_token = token_response["result"]["access_token"]

    data = req.json

    body = {
        "properties": [
            {
                "code": data.get("code"),          # ex: switch_1
                "custom_name": data.get("name")    # ex: Pompe champ nord
            }
        ]
    }

    path = f"/v2.0/cloud/thing/{device_id}/shadow/properties"

    res = call_tuya_api(
        method="POST",
        path=path,
        access_token=access_token,
        body=body
    )

    return jsonify(res)


# Etat de la pompe en direct

@pompe_bp.route("/device/<device_id>/status", methods=["GET"])
def get_status(device_id):

    # 1. TOKEN
    token_response = get_tuya_token()

    if not token_response.get("success"):
        return jsonify(token_response), 400

    access_token = token_response["result"]["access_token"]

    # 2. API PATH
    path = f"/v2.0/cloud/thing/{device_id}/shadow/properties"

    # 3. CALL TUYA
    res = call_tuya_api(
        method="GET",
        path=path,
        access_token=access_token
    )

    return jsonify(res)

# IRRIGATION AUTOMATIQUE
@pompe_bp.route("/device/<device_id>/action", methods=["POST"])
def send_action(device_id):

    token_response = get_tuya_token()

    if not token_response.get("success"):
        return jsonify(token_response), 400

    access_token = token_response["result"]["access_token"]

    data = req.json

    body = {
        "code": data.get("code"),
        "input_params": data.get("input_params")
    }

    path = f"/v2.0/cloud/thing/{device_id}/shadow/actions"

    res = call_tuya_api(
        method="POST",
        path=path,
        access_token=access_token,
        body=body
    )

    return jsonify(res)