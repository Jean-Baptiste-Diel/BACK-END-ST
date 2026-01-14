import os
from flask import Blueprint, jsonify, current_app, request
import requests
from api.config.model import User  # ton modèle SQLAlchemy

bp_meteo = Blueprint('meteo', __name__)

API_KEY = os.environ.get('WEATHER_API_KEY')
URL = "https://api.openweathermap.org/data/2.5/weather"

def get_meteo(city: str):
    """Appel OpenWeatherMap"""
    params = {
        "q": city,
        "appid": API_KEY,
        "units": "metric",
        "lang": "fr"
    }
    response = requests.get(URL, params=params)
    if response.status_code != 200:
        current_app.logger.warning(f"Erreur OpenWeather: {response.text}")
        return None, response.status_code
    return response.json(), 200

def return_meteo(city: str):
    """Format JSON pour Flutter"""
    data, status = get_meteo(city)
    if data is None:
        return jsonify({"error": "Impossible de récupérer la météo"}), status
    result = {
        "ville": data["name"],
        "temperature": data["main"]["temp"],
        "description": data["weather"][0]["description"],
        "humidite": data["main"]["humidity"],
        "pressure": data["main"]["pressure"]
    }
    current_app.logger.info(f"Météo récupérée pour: {city}")
    return jsonify(result), 200

# Météo de l'utilisateur connecté via id_user
@bp_meteo.route('/meteo', methods=['GET'])
def meteo_user_by_id():
    user_id = request.args.get("id_user")
    if not user_id:
        current_app.logger.info("error: id_user manquant")
        return jsonify({"error": "id_user manquant"}), 400
    try:
        user_id = int(user_id)
    except ValueError:
        current_app.logger.info("error: id_user invalide")
        return jsonify({"error": "id_user invalide"}), 400
    user = User.query.get(user_id)
    if not user or not user.location:
        current_app.logger.info("error: Utilisateur ou ville introuvable")
        return jsonify({"error": "Utilisateur ou ville introuvable"}), 404

    return return_meteo(user.location)

# Météo pour n'importe quelle ville passée en paramètre
@bp_meteo.route('/meteo/<string:location>', methods=['GET'])
def meteo_location(location: str):
    return return_meteo(location)

@bp_meteo.route('/meteos', methods=['GET'])
def meteo_location():
    return return_meteo("Dakar")