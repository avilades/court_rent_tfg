import random
import os
import requests
from datetime import datetime, date as dt_date
import logging
#from dotenv import load_dotenv
from dotenv import dotenv_values
from .conf.config_json import initialize_weather


# Cargar variables de entorno desde el archivo .env si existe
# load_dotenv()
config = dotenv_values(".env")
#config_json.leer_config("./app/conf/config.json")

# Configuración del logger para este módulo
logger = logging.getLogger(__name__)


# Configuración de OpenWeatherMap
LATITUD = initialize_weather()[0]  # Latitud de Madrid
LONGITUD = initialize_weather()[1] # Longitud de Madrid

# Se recomienda configurar esta clave en las variables de entorno
#OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "RANDOM")
OPENWEATHER_API_KEY = config["OPENWEATHER_API_KEY"]

logger.info(f"OPENWEATHER_API_KEY: {OPENWEATHER_API_KEY}")

def get_weather_prediction(date_str: str):
    """
    Obtiene la predicción meteorológica para Madrid para una fecha específica.
    Usa la API de OpenWeatherMap (5 day / 3 hour forecast).
    """
    logger.debug(f"OpenWeatherMap LATITUD: {LATITUD}")
    logger.debug(f"OpenWeatherMap LONGITUD: {LONGITUD}")


    try:
        target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        
        # Si no hay API KEY configurada, usamos el mock
        if OPENWEATHER_API_KEY == "RANDOM" or not OPENWEATHER_API_KEY:
            logger.warning("No se ha detectado OPENWEATHER_API_KEY. Usando datos simulados.")
            return _get_mock_weather(target_date)

        # Llamada a la API de previsión (5 días / 3 horas)
        url = f"http://api.openweathermap.org/data/2.5/forecast?lat={LATITUD}&lon={LONGITUD}&appid={OPENWEATHER_API_KEY}&units=metric&lang=es"
        logger.info(f"Llamada a OpenWeatherMap: {url}")
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        logger.info(f"Respuesta de OpenWeatherMap: {data}")

        # Buscamos la previsión más cercana a las 12:00 del mediodía de la fecha solicitada
        best_match = None
        min_diff = float('inf')

        for entry in data.get('list', []):
            forecast_dt = datetime.fromtimestamp(entry['dt'])
            if forecast_dt.date() == target_date:
                # Calculamos la diferencia con las 12:00 PM
                diff = abs((forecast_dt - datetime.combine(target_date, datetime.min.time().replace(hour=12))).total_seconds())
                if diff < min_diff:
                    min_diff = diff
                    best_match = entry

        if best_match:
            weather_data = best_match['weather'][0]
            main_data = best_match['main']
            
            # Mapeo de iconos de OpenWeather a los de nuestra app
            icon_map = {
                "01": "☀️", # sky
                "02": "⛅", # few clouds
                "03": "☁️", # scattered clouds
                "04": "☁️", # broken clouds
                "09": "🌧️", # shower rain
                "10": "🌦️", # rain
                "11": "⛈️", # thunderstorm
                "13": "❄️", # snow
                "50": "🌫️"  # mist
            }
            ow_icon = weather_data['icon'][:2]
            icon = icon_map.get(ow_icon, "❓")
            
            weather_report = {
                "temperature": round(main_data['temp']),
                "description": weather_data['description'].capitalize(),
                "icon": icon,
                "is_rainy": ow_icon in ["09", "10", "11"],
                "is_snowy": ow_icon in ["13"],
                "is_cloudy": ow_icon in ["02", "03", "04"],
                "is_foggy": ow_icon in ["50"]
            }   
            logger.info(f"Weather prediction for {date_str}: {weather_report}")
            return weather_report

        else:
            # Si la fecha está fuera del rango de 5 días, usamos el mock
            logger.info(f"Fecha {date_str} fuera del rango de previsión de 5 días. Usando datos simulados.")
            return _get_mock_weather(target_date)

    except Exception as e:
        logger.error(f"Error al llamar a OpenWeatherMap: {e}")
        return {
            "temperature": "N/A",
            "description": "Error al obtener clima",
            "icon": "❓",
            "is_rainy": False,
            "is_snowy": False,
            "is_cloudy": False,
            "is_foggy": False
        }

def _get_mock_weather(target_date: dt_date):
    """Genera una predicción simulada (Legacy/Fallback)"""
    random.seed(target_date.toordinal())
    temp = random.randint(10, 30)
    weathers = [
        {"description": "Soleado", "icon": "☀️", "is_rainy": False},
        {"description": "Parcialmente nublado", "icon": "⛅", "is_rainy": False},
        {"description": "Nublado", "icon": "☁️", "is_rainy": False},
        {"description": "Lluvia ligera", "icon": "🌦️", "is_rainy": True},
        {"description": "Chubascos", "icon": "🌧️", "is_rainy": True}
    ]
    prediction = random.choice(weathers)
    return {
        "temperature": temp,
        "description": prediction["description"],
        "icon": prediction["icon"],
        "is_rainy": prediction["is_rainy"],
        "is_snowy": prediction["is_snowy"],
        "is_cloudy": prediction["is_cloudy"],
        "is_foggy": prediction["is_foggy"]
    }
