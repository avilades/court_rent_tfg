import os
import logging
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime
from .conf.config_json import initialize_logger_config
initialize_logger_config()

def setup_logging():
    """
    Configura el registro de logs con rotación diaria.
    Los logs se almacenan en el directorio 'logs' con el formato court_reservation_YYYYMMDD.log
    """
    log_dir = "logs"
    # Aseguramos que la carpeta de logs exista
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Nombre base del archivo de log
    log_base = os.path.join(log_dir, "court_reservation.log")

    # TimedRotatingFileHandler: rota el archivo automáticamente.
    # 'midnight': rota a la medianoche.
    # backupCount=30: mantenemos los logs de los últimos 30 días.
    handler = TimedRotatingFileHandler(
        log_base,
        when="midnight",
        interval=1,
        backupCount=30,
        encoding="utf-8"
    )

    # Sufijo personalizado para los archivos rotados (YYYYMMDD)
    handler.suffix = "%Y%m%d"

    # Función personalizada para renombrar los archivos rotados
    def namer(default_name):
        """
        Cambia el formato por defecto de SQLAlchemy/Python (archivo.log.fecha)
        a un formato más estándar (archivo_fecha.log).
        """
        # default_name suele ser algo como "logs/court_reservation.log.20260113"
        if ".log." in default_name:
            parts = default_name.split(".log.")
            return f"{parts[0]}_{parts[1]}.log"
        return default_name

    handler.namer = namer

    # Configuración global del logger raíz
    logging.basicConfig(
        #level definimos el nivel de logado DEBUG, INFO, WARNING, ERROR, CRITICAL
        #level=getattr(initialize_logger_config(), "LOG_LEVEL", "INFO"),
        level=initialize_logger_config()[0],
        #level=LOG_LEVEL if LOG_LEVEL else logging.INFO,
        format=initialize_logger_config()[4],
        #format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        #format="%(asctime)s -- %(filename)s -- %(funcName)s -- %(levelname)s -- %(levelno)s -- %(lineno)d -- %(message)s -- %(module)s -- name: %(name)s -- pathname: %(pathname)s --process: %(process)d -- processName: %(processName)s -- thread: %(thread)d -- threadName: %(threadName)s -- taskName: %(taskName)s -- lineNum: %(lineno)d",
        #format="%(asctime)s -- %(filename)s -- %(funcName)s -- %(levelname)s --levelNum: %(levelno)s --lineNum: %(lineno)d -- %(message)s -- module: %(module)s -- name: %(name)s -- pathname: %(pathname)s --process: %(process)d -- taskName: %(taskName)s -- lineNum: %(lineno)d",
        handlers=[
            handler
        ],
        force=True # Forzamos la configuración si ya existía una previa
    )
    
    logging.info("\n\n\n\n")
    logging.info(f"Sistema de logs inicializado. Los archivos se guardarán en la carpeta:  {log_base}")
