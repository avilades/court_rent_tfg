"""
Archivo de carga de configuraciones
Aqui almacenamos en variables globales las configuraciones del archivo config.json
Que luego se usan en el resto de la aplicacion, al importar este archivo
"""

import json


def leer_config(config_file):
    """
    funcion para leer el archivo de config

    parametros:\n
    - archivo y ruta\n
    """
    with open(config_file, "r") as j:
        config_data = json.load(j)
        OPENWEATHER_API_KEY = config_data["open_weather_api_key"]
        RUTA_CARPETA_CANCHAS = config_data["ruta_carpeta_canchas"]