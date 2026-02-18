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
    Función para leer el archivo de configuración completo.

    Parámetros:
    - config_file: Ruta al archivo de configuración.

    Retorna:
    - config_data: Diccionario con los datos del archivo de configuración.
    """
    with open(config_file, "r", encoding="utf-8") as j:
        config_data = json.load(j)
        logger.info("Archivo de configuración leído correctamente")
        return config_data


def initialize_lat_lon():
    """
    Inicializa las variables globales de latitud y longitud.
    """
    global LATITUD, LONGITUD
    config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
    config_data = leer_config(config_file)

    LATITUD = config_data.get("latitud")
    LONGITUD = config_data.get("longitud")

    logger.debug(f"Latitud: {LATITUD}, Longitud: {LONGITUD}")
    logger.info("Variables de latitud y longitud inicializadas")

    return LATITUD, LONGITUD


def initialize_logger_config():
    """
    Inicializa las variables globales relacionadas con la configuración del logger.
    """
    global LOG_LEVEL, LOG_DIR, LOG_FILE_NAME, BACKUP_COUNT, LOG_FORMAT
    config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
    config_data = leer_config(config_file)

    log_config = config_data.get("log_config", {})
    LOG_LEVEL = log_config.get("log_level", "INFO")
    LOG_DIR = log_config.get("log_dir", "logs")
    LOG_FILE_NAME = log_config.get("log_file_name", "app.log")
    BACKUP_COUNT = log_config.get("backup_count", 30)
    LOG_FORMAT = log_config.get("log_format", "%(asctime)s - %(levelname)s - %(message)s")

    logger.debug(f"LOG_LEVEL: {LOG_LEVEL}, LOG_DIR: {LOG_DIR}, LOG_FILE_NAME: {LOG_FILE_NAME}")
    logger.info("Configuración del logger inicializada")

    return LOG_LEVEL, LOG_DIR, LOG_FILE_NAME, BACKUP_COUNT, LOG_FORMAT



# Inicializamos las variables globales al importar el módulo
LATITUD, LONGITUD = None, None
LOG_LEVEL, LOG_DIR, LOG_FILE_NAME, BACKUP_COUNT, LOG_FORMAT = None, None, None, None, None

if __name__ == "__main__":
    initialize_lat_lon()
    initialize_logger_config()
