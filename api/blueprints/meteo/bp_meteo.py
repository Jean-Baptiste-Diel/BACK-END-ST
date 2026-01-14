import os

from flask import Blueprint, jsonify, current_app
import requests

bp_meteo = Blueprint('meteo', __name__)

API_KEY =os.environ.get('WEATHER_API_KEY')
URL = "https://api.openweathermap.org/data/2.5/weather"

def get_meteo():
    city = "Kolda"
    params = {
        "q": city,
        "appid": API_KEY,
        "units": "metric",
        "lang": "fr"
    }
    response = requests.get(URL, params=params)
    if response.status_code != 200:
        return None, response.status_code
    return response.json(), 200

@bp_meteo.route('/meteo', methods=['GET'])
def meteo():
    data, status = get_meteo()

    if data is None:
        current_app.logger.warning(f'Impossible de récupérer la météo: {status}')
        return jsonify({"error": "Impossible de récupérer la météo"}), status

    result = {
        "ville": data["name"],
        "temperature": data["main"]["temp"],
        "description": data["weather"][0]["description"],
        "humidite": data["main"]["humidity"]
    }
    current_app.logger.info('Récupération la météo')
    return jsonify(result), 200
