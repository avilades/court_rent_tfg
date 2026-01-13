import os
import logging
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime

def setup_logging():
    """
    Configures daily rotating file logging.
    Logs are stored in the 'logs' directory with the format court_reservation_YYYYMMDD.log
    """
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Base filename for the logger
    log_base = os.path.join(log_dir, "court_reservation.log")

    # TimedRotatingFileHandler: rotates every midnight
    handler = TimedRotatingFileHandler(
        log_base,
        when="midnight",
        interval=1,
        backupCount=30,
        encoding="utf-8"
    )

    # Custom suffix for the rotated files (will be appended with a dot by the handler)
    handler.suffix = "%Y%m%d"

    # Custom namer to ensure the format is exactly court_reservation_YYYYMMDD.log
    def namer(default_name):
        # default_name is usually "logs/court_reservation.log.20260113"
        # We want "logs/court_reservation_20260113.log"
        if ".log." in default_name:
            parts = default_name.split(".log.")
            return f"{parts[0]}_{parts[1]}.log"
        return default_name

    handler.namer = namer

    # Configure the root logger
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            handler
        ],
        force=True
    )
    
    logging.info("Logging initialized. Logs will be saved to the 'logs' directory.")
