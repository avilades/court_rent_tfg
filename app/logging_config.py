import os
import logging
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime

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
        level=logging.INFO, # Nivel mínimo de severidad a registrar
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            handler
        ],
        force=True # Forzamos la configuración si ya existía una previa
    )
    
    logging.info("Sistema de logs inicializado. Los archivos se guardarán en la carpeta 'logs'.")
