import requests
from flask import Blueprint, request, jsonify

from api.utils.token import get_vanne_token

vanne_bp = Blueprint("vanne_bp", __name__)

# Endpoint pour récupérer un token (facultatif si utilisé uniquement en interne)
@vanne_bp.route("/token", methods=["POST", "GET"])
def vanne_token():
    token = get_vanne_token()
    return {"token": token}

API_URL = "http://smart1688.net/prod_api/api/device/info/getDeviceListBackend"

# Fonction pour construire les headers comme en Dart
def get_headers(user_id=None, open_token=None):
    headers = {
        "Content-Type": "application/json",
    }
    if user_id:
        headers["UserId"] = str(user_id)
    if open_token:
        headers["open_token"] = open_token
    return headers

# Fonction pour récupérer la liste des devices
def get_device_list_backend(params, user_id=None):
    """
    params: dictionnaire optionnel avec clés
        imeiCode, deviceName, deviceType, deviceStatus, page (dict)
    """
    # Récupération du token si nécessaire
    token_data = get_vanne_token()
    if token_data["status"] != "success":
        return {"error": token_data.get("error", {}), "status": "fail"}

    open_token = token_data["token"]

    # Construction du body JSON conditionnel
    body = {}
    if params.get("params"):
        body["params"] = {k: v for k, v in params["params"].items() if v is not None}
    if params.get("page"):
        body["page"] = params["page"]

    headers = get_headers(user_id=user_id, open_token=open_token)

    try:
        r = requests.post(API_URL, json=body, headers=headers, timeout=10)
        data = r.json()
        print("Request body:", body)
        print("Status:", r.status_code)
        print("Response:", r.text)

        if data.get("tx_code") == "00":
            return {"status": "success", "tx_code": data["tx_code"], "data": data.get("data"), "page": data.get("page")}
        else:
            return {"status": "fail", "error": data.get("error_info", {})}

    except requests.exceptions.RequestException as e:
        return {"status": "fail", "error": str(e)}


# Endpoint Flask
@vanne_bp.route("/device/list", methods=["POST"])
def device_list():
    """
    Attends un JSON similaire à :
    {
        "userId": "123",
        "params": {
            "imeiCode": "xxx",
            "deviceName": "Vanne",
            "deviceType": "00",
            "deviceStatus": "60"
        },
        "page": {
            "page_num": 0,
            "page_size": 10
        }
    }
    """
    req_data = request.get_json() or {}
    user_id = req_data.get("userId")
    params = {
        "params": req_data.get("params"),
        "page": req_data.get("page")
    }

    result = get_device_list_backend(params=params, user_id=user_id)
    return jsonify(result)