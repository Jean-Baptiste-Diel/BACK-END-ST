import requests
from flask import Blueprint, request, jsonify
from api.utils.token import get_vanne_token, refresh_vanne_token

vanne_bp = Blueprint("vanne_bp", __name__)

BASE_URL = "http://smart1688.net/prod_api"


# =========================
# HEADERS
# =========================
def get_headers(user_id=None, open_token=None):
    headers = {
        "Content-Type": "application/json",
    }

    if user_id:
        headers["UserId"] = str(user_id)

    if open_token:
        headers["open_token"] = open_token

    return headers


# =========================
# CORE API CALL
# =========================
def post_to_api(endpoint, body=None, user_id=None, retry=True):

    token_data = get_vanne_token()

    if token_data.get("status") != "success":
        return token_data

    open_token = token_data.get("token")
    if not open_token:
        return {"status": "fail", "error": "missing_token"}

    headers = get_headers(user_id=user_id, open_token=open_token)

    try:
        r = requests.post(
            f"{BASE_URL}{endpoint}",
            json=body or {},
            headers=headers,
            timeout=10
        )

        try:
            data = r.json()
        except Exception:
            return {
                "status": "fail",
                "error": "invalid_json_response",
                "raw": r.text
            }

        print("📡 RESPONSE:", data)

        # =========================
        # SAFE ERROR EXTRACTION
        # =========================
        error_info = data.get("error_info") or {}
        error = data.get("error") or {}

        error_code = None

        if isinstance(error, dict):
            error_code = error.get("code")

        if isinstance(error_info, dict):
            error_code = error_code or error_info.get("code")

        # =========================
        # TOKEN EXPIRED → REFRESH
        # =========================
        if error_code == "401" and retry:
            print("🔄 Token invalide → refresh")

            refresh_vanne_token()

            return post_to_api(endpoint, body, user_id, retry=False)

        # =========================
        # SUCCESS
        # =========================
        if data.get("tx_code") == "00":
            return {
                "status": "success",
                "data": data.get("data"),
                "page": data.get("page")
            }

        # =========================
        # FAIL SAFE
        # =========================
        return {
            "status": "fail",
            "error": error_info or error or data
        }

    except Exception as e:
        return {
            "status": "fail",
            "error": str(e)
        }


# =========================
# ROUTES
# =========================

@vanne_bp.route("/device/list", methods=["POST"])
def device_list():
    req = request.get_json() or {}

    return jsonify(
        post_to_api(
            "/api/device/info/getDeviceListBackend",
            body={
                "params": req.get("params", {}),
                "page": req.get("page", {
                    "page_num": 0,
                    "page_size": 10
                })
            },
            user_id=req.get("userId")
        )
    )


@vanne_bp.route("/device/details", methods=["POST"])
def device_details():
    req = request.get_json() or {}

    return jsonify(
        post_to_api(
            "/api/device/info/getDeviceInfo",
            body={
                "imeiCode": req.get("imeiCode")
            },
            user_id=req.get("userId")
        )
    )