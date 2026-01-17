"""
Archivo de carga de configuraciones
Aqui almacenamos en variables globales las configuraciones del archivo config.json
Que luego se usan en el resto de la aplicacion, al importar este archivo
"""
import logging
import json
import os

# Configuración del logger para este módulo
logger = logging.getLogger(__name__)



def leer_config(config_file):
    """
    funcion para leer el archivo de config

    parametros:\n
    - archivo y ruta\n
    """
    
    with open(config_file, "r", encoding="utf-8") as j:
        config_data = json.load(j)
        LATITUD = config_data["latitud"]
        LONGITUD = config_data["longitud"]

        return LATITUD, LONGITUD


def initialize_weather():
    logger.info("Inicializando variables globales")
    global LATITUD, LONGITUD
    LATITUD, LONGITUD = leer_config(os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json"))
    logger.debug("Latitud: {}".format(LATITUD))
    logger.debug("Longitud: {}".format(LONGITUD))
    logger.info("Variables globales inicializadas")
    return LATITUD, LONGITUD







# Inicializamos las variables globales al importar el modulo
LATITUD, LONGITUD = None, None
if __name__ == "__main__":
    initialize_weather()
