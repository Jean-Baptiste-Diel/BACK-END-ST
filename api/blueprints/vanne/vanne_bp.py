import requests
from flask import Blueprint, request, jsonify
from api.utils.token import get_vanne_token
from upstash_redis import Redis
import os

vanne_bp = Blueprint("vanne_bp", __name__)

BASE_URL = "http://smart1688.net/prod_api"
CACHE_TTL = 86400  # 24h en secondes

REDIS_URL = os.getenv("REDIS_URL")
REDIS_TOKEN = os.getenv("REDIS_TOKEN")
redis_client = Redis(url=REDIS_URL, token=REDIS_TOKEN)

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

# REDIS CACHE
def set_cache(token, user_id):
    """Sauvegarde token + user id pendant 24h"""
    redis_client.set("smart_token", token, ex=CACHE_TTL)
    redis_client.set("smart_user_id", user_id, ex=CACHE_TTL)

def clear_cache():
    """Supprime le cache"""
    redis_client.delete("smart_token")
    redis_client.delete("smart_user_id")

def get_cached_auth():
    """Récupère depuis Upstash Redis"""
    token = redis_client.get("smart_token")
    user_id = redis_client.get("smart_user_id")

    if token and user_id:
        return {
            "status": "success",
            "token": token,
            "user_id": user_id,
            "cached": True
        }

    return None

# REFRESH CACHE
def refresh_auth_cache():
    """Appelle l'API externe et met Redis à jour"""
    token_data = get_vanne_token()

    if token_data["status"] != "success":
        return {
            "status": "fail",
            "error": token_data.get("error", {})
        }

    token = token_data["token"]
    headers = get_headers(open_token=token)

    try:
        r = requests.post(
            f"{BASE_URL}/api/user/info/user_info",
            json={
                "page": {"page_num": 0, "page_size": 10},
                "params": ""
            },
            headers=headers,
            timeout=10
        )

        data = r.json()

        if data.get("tx_code") != "00":
            return {"status": "fail", "error": data.get("error_info", data)}

        user_id = data["data"]["id"]

        # Sauvegarde Upstash Redis
        set_cache(token, user_id)

        return {
            "status": "success",
            "token": token,
            "user_id": user_id,
            "cached": False
        }

    except Exception as e:
        return {"status": "fail", "error": str(e)}

def get_auth_data():
    """1) regarde Redis 2) sinon refresh"""
    cached = get_cached_auth()
    if cached:
        return cached
    return refresh_auth_cache()

# =========================
# API CALL
# =========================
def post_to_api(endpoint, body=None):
    auth = get_auth_data()

    if auth["status"] != "success":
        return auth

    headers = get_headers(user_id=auth["user_id"], open_token=auth["token"])

    try:
        r = requests.post(f"{BASE_URL}{endpoint}", json=body or {}, headers=headers, timeout=10)
        data = r.json()

        if data.get("tx_code") == "00":
            return {"status": "success", "tx_code": data.get("tx_code"), "data": data.get("data"), "page": data.get("page")}

        return {"status": "fail", "error": data.get("error_info", data)}

    except Exception as e:
        return {"status": "fail", "error": str(e)}

# =========================
# ROUTES
# =========================
@vanne_bp.route("/token", methods=["GET", "POST"])
def token():
    return jsonify(get_auth_data())

@vanne_bp.route("/device/list", methods=["POST"])
def device_list():
    req_data = request.get_json() or {}
    result = post_to_api(
        "/api/device/info/getDeviceListBackend",
        body={"params": req_data.get("params", {}), "page": req_data.get("page", {"page_num": 0, "page_size": 10})}
    )
    return jsonify(result)

@vanne_bp.route("/device/details", methods=["POST"])
def device_details():
    req_data = request.get_json() or {}
    result = post_to_api("/api/device/info/getDeviceInfo", body={"imeiCode": req_data.get("imeiCode")})
    return jsonify(result)

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
            "workMinDuration": req_data.get("workMinDuration", 0),
        }
    )
    return jsonify(result)

@vanne_bp.route("/cache/refresh", methods=["POST"])
def refresh_cache():
    clear_cache()
    return jsonify(refresh_auth_cache())