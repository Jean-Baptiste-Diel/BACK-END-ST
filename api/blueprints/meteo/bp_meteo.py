import os
import time
import requests
from flask import Blueprint, jsonify, current_app, request
from api.config.model import User

bp_meteo = Blueprint("meteo", __name__)

API_KEY = os.environ.get("WEATHER_API_KEY")
URL = "https://api.openweathermap.org/data/2.5/weather"

# CACHE MÉTÉO (10 minutes)
METEO_CACHE = {}
CACHE_TTL = 600

# LOGIQUE IRRIGATION
def compute_irrigation(temp, humidity, wind, rain):
    gravite = 1
    message = "Conditions normales : Vous pouvez irriguer normalement."

    if rain >= 5:
        gravite = 2
        message = "Pluie récente : irrigation réduite recommandée."
    if rain >= 20:
        gravite = 3
        message = "Pluie abondante : irrigation non nécessaire."
    if wind >= 8:
        gravite = max(gravite, 2)
        message = "Vent fort : éviter l'irrigation prolongée."
    if humidity >= 85:
        gravite = max(gravite, 2)
        message = "Humidité élevée : irrigation limitée."
    if rain >= 20 and humidity >= 85:
        gravite = 3
        message = "Sol saturé : irrigation arrêtée."

    return gravite, message

# APPEL OPENWEATHER
def get_meteo(city: str):
    if not API_KEY:
        current_app.logger.error("WEATHER_API_KEY manquante")
        return None, 500

    now = int(time.time())
    city_key = city.lower()

    # Cache
    if city_key in METEO_CACHE:
        cached = METEO_CACHE[city_key]
        if now < cached["expires_at"]:
            return cached["data"], 200

    params = {
        "q": city.strip(),
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

# FORMAT MÉTÉO POUR FLUTTER
def return_meteo(city: str):
    data, status = get_meteo(city)

    if data is None:
        return jsonify({
            "error": "Impossible de récupérer la météo",
            "ville": city
        }), status

    wind = data.get("wind", {}) or {}
    rain = data.get("rain", {}) or {}

    vent_ms = float(wind.get("speed") or 0.0)

    pluie_mm = rain.get("1h")
    if pluie_mm is None:
        pluie_mm = rain.get("3h")
    pluie_mm = float(pluie_mm or 0.0)

    temp = float(data["main"]["temp"])
    humidity = int(data["main"]["humidity"])

    # Calcul irrigation
    gravite, message_irrigation = compute_irrigation(
        temp=temp,
        humidity=humidity,
        wind=vent_ms,
        rain=pluie_mm
    )

    result = {
        "ville": data.get("name"),
        "temperature": round(temp, 1),
        "description": data["weather"][0]["description"].capitalize(),
        "humidite": humidity,
        "pression": data["main"]["pressure"],
        "icone": data["weather"][0]["icon"],
        "vent": round(vent_ms, 1),
        "pluie": round(pluie_mm, 1),

        # Irrigation intelligente
        "gravite": gravite,
        "message_irrigation": message_irrigation
    }

    current_app.logger.info(f"Météo récupérée : {city}")
    return jsonify(result), 200

# MÉTÉO PAR UTILISATEUR
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

# MÉTÉO PAR VILLE
@bp_meteo.route("/meteo/<string:location>", methods=["GET"])
def meteo_location(location: str):
    return return_meteo(location)

# MÉTÉO PAR DÉFAUT (TEST)
@bp_meteo.route("/meteos", methods=["GET"])
def meteos_locations():
    return return_meteo("Dakar")
