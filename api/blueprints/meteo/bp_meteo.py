import os
import time
import requests
from flask import Blueprint, jsonify, current_app, request
from api.config.model import User

bp_meteo = Blueprint("meteo", __name__)

API_KEY = os.environ.get("WEATHER_API_KEY")
URL = "https://api.openweathermap.org/data/2.5/weather"

# ===============================
# ⏱️ CACHE MÉTÉO (10 minutes)
# ===============================
METEO_CACHE = {}  # { city: {data, expires_at} }
CACHE_TTL = 600  # secondes

# ===============================
# 🌦️ APPEL OPENWEATHER
# ===============================
def get_meteo(city: str):
    if not API_KEY:
        current_app.logger.error("WEATHER_API_KEY manquante")
        return None, 500

    now = int(time.time())

    city_key = city.lower()

    # ✅ cache
    if city_key in METEO_CACHE:
        cached = METEO_CACHE[city_key]
        if now < cached["expires_at"]:
            return cached["data"], 200

    params = {
        "q": city,
        "appid": API_KEY,
        "units": "metric",
        "lang": "fr"
    }

    try:
        response = requests.get(URL, params=params, timeout=5)
    except requests.exceptions.RequestException as e:
        current_app.logger.warning(f"Erreur réseau météo: {e}")
        return None, 503

    if response.status_code != 200:
        current_app.logger.warning(
            f"Erreur OpenWeather ({response.status_code}): {response.text}"
        )
        return None, response.status_code

    data = response.json()

    METEO_CACHE[city_key] = {
        "data": data,
        "expires_at": now + CACHE_TTL
    }

    return data, 200

# ===============================
# 🎯 FORMAT JSON POUR FLUTTER
# ===============================
def return_meteo(city: str):
    data, status = get_meteo(city)

    if data is None:
        return jsonify({
            "error": "Impossible de récupérer la météo",
            "city": city
        }), status

    result = {
        "ville": data.get("name"),
        "temperature": data["main"]["temp"],
        "description": data["weather"][0]["description"],
        "humidite": data["main"]["humidity"],
        "pression": data["main"]["pressure"],
        "icone": data["weather"][0]["icon"]
    }

    current_app.logger.info(f"🌦️ Météo récupérée : {city}")
    return jsonify(result), 200

# ===============================
# 👤 MÉTÉO UTILISATEUR
# ===============================
@bp_meteo.route("/meteo", methods=["GET"])
def meteo_user_by_id():
    user_id = request.args.get("id_user")

    if not user_id:
        return jsonify({"error": "id_user manquant"}), 400

    try:
        user_id = int(user_id)
    except ValueError:
        return jsonify({"error": "id_user invalide"}), 400

    user = User.query.get(user_id)

    if not user or not user.location:
        return jsonify({"error": "Utilisateur ou ville introuvable"}), 404

    return return_meteo(user.location)

# ===============================
# 🌍 MÉTÉO PAR VILLE
# ===============================
@bp_meteo.route("/meteo/<string:location>", methods=["GET"])
def meteo_location(location: str):
    return return_meteo(location)

# ===============================
# 🇸🇳 DEFAULT (DAKAR)
# ===============================
@bp_meteo.route("/meteos", methods=["GET"])
def meteos_locations():
    return return_meteo("Dakar")
