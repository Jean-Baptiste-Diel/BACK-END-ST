import requests
from flask import Blueprint, request, jsonify
from api.utils.token import get_vanne_token

vanne_bp = Blueprint("vanne_bp", __name__)

BASE_URL = "http://smart1688.net/prod_api"

# UTILITAIRES
def get_headers(user_id=None, open_token=None):
    headers = {
        "Content-Type": "application/json"
    }

    if user_id:
        headers["UserId"] = str(user_id)

    if open_token:
        headers["open_token"] = open_token

    return headers


def get_token():
    token_data = get_vanne_token()

    if token_data["status"] != "success":
        return None, {"status": "fail", "error": token_data.get("error", {})}

    return token_data["token"], None


def post_to_api(endpoint, body=None, user_id=None):
    open_token, error = get_token()

    if error:
        return error

    headers = get_headers(user_id=user_id, open_token=open_token)

    try:
        r = requests.post(
            f"{BASE_URL}{endpoint}",
            json=body or {},
            headers=headers,
            timeout=10
        )

        data = r.json()

        print("URL:", endpoint)
        print("BODY:", body)
        print("STATUS:", r.status_code)
        print("RESPONSE:", r.text)

        if data.get("tx_code") == "00":
            return {
                "status": "success",
                "tx_code": data.get("tx_code"),
                "data": data.get("data"),
                "page": data.get("page")
            }

        return {
            "status": "fail",
            "error": data.get("error_info", data)
        }

    except Exception as e:
        return {"status": "fail", "error": str(e)}

# TOKEN
@vanne_bp.route("/token", methods=["GET", "POST"])
def token():
    return jsonify(get_vanne_token())

# USER INFO
@vanne_bp.route("/user/info", methods=["POST"])
def user_info():
    return jsonify(
        post_to_api(
            "/api/user/info/user_info",
            body={
                "page": {
                    "page_num": 0,
                    "page_size": 10
                },
                "params": ""
            }
        )
    )

# DEVICE LIST
@vanne_bp.route("/device/list", methods=["POST"])
def device_list():
    req_data = request.get_json() or {}

    result = post_to_api(
        "/api/device/info/getDeviceListBackend",
        body={
            "params": req_data.get("params", {}),
            "page": req_data.get("page", {
                "page_num": 0,
                "page_size": 10
            })
        },
        user_id=req_data.get("userId")
    )

    return jsonify(result)

# DEVICE DETAILS
@vanne_bp.route("/device/details", methods=["POST"])
def device_details():

    req_data = request.get_json() or {}

    result = post_to_api(
        "/api/device/info/getDeviceInfo",
        body={
            "imeiCode": req_data.get("imeiCode")
        },
        user_id=req_data.get("userId")
    )

    return jsonify(result)

# PUMP LIST
@vanne_bp.route("/pump/list", methods=["POST"])
def pump_list():
    req_data = request.get_json() or {}
    result = post_to_api(
        "/api/device/info/getPumpDeviceList",
        body={
            "params": req_data.get("params", {}),
            "page": req_data.get("page", {
                "page_num": 0,
                "page_size": 10
            })
        },
        user_id=req_data.get("userId")
    )
    return jsonify(result)

# OPEN / CLOSE VALVE
@vanne_bp.route("/device/control", methods=["POST"])
def control_device():
    req_data = request.get_json() or {}

    result = post_to_api(
        "/api/task/group/save-single",
        body={
            "deviceId": req_data.get("deviceId"),
            "controlType": req_data.get("controlType", "00"),
            "percentage": req_data.get("percentage", 100),
            "workHourDuration": req_data.get("workHourDuration", 0),
            "workMinDuration": req_data.get("workMinDuration", 0)
        },
        user_id=req_data.get("userId")
    )

    return jsonify(result)

# SCHEDULE TASK
@vanne_bp.route("/device/schedule/add", methods=["POST"])
def add_schedule():
    req_data = request.get_json() or {}

    result = post_to_api(
        "/api/task/timing/add",
        body=req_data,
        user_id=req_data.get("userId")
    )

    return jsonify(result)

# DELETE TASK
@vanne_bp.route("/device/schedule/delete", methods=["POST"])
def delete_schedule():
    req_data = request.get_json() or {}

    result = post_to_api(
        "/api/task/timing/batch-del",
        body=req_data,
        user_id=req_data.get("userId")
    )

    return jsonify(result)

# DEVICE LOGS
@vanne_bp.route("/device/logs", methods=["POST"])
def device_logs():
    req_data = request.get_json() or {}

    result = post_to_api(
        "/api/device/log/page_list",
        body=req_data,
        user_id=req_data.get("userId")
    )
    return jsonify(result)