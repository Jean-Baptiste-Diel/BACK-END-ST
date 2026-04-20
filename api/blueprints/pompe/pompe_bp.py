from flask import Blueprint, jsonify

from api.crud.crud_pompe.pompe import get_devices
from api.utils.token import get_tuya_token

pompe_bp = Blueprint("pompe_bp", __name__)

# GET DEVICES ROUTE
@pompe_bp.route("/devices/pompes", methods=["GET"])
def devices_route():

    token_response = get_tuya_token()

    if not token_response.get("success"):
        return jsonify(token_response), 400

    access_token = token_response["result"]["access_token"]
    uid = token_response["result"]["uid"]

    devices = get_devices(access_token, uid)

    return jsonify(devices)