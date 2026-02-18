#!/usr/bin/env python3
"""
Worker que procesa tareas programadas pendientes.

Este script debe correrse en paralelo con la aplicación principal.
Periódicamente revisa la BD y procesa tareas que están listas para ejecutarse.

Uso:
    python app/workers/task_worker.py

O en Docker:
    docker-compose up -d app
    docker run --network court_rent_network -e DATABASE_URL=... court_rent python app/workers/task_worker.py
"""

import time
import logging
import sys
import os
from datetime import datetime, timedelta

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Agregar el directorio padre al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import database
from app.services.task_service import process_pending_tasks, get_task_statistics

# Configuración
POLL_INTERVAL_SECONDS = 60  # Revisar cada 60 segundos
MAX_CONSECUTIVE_ERRORS = 5  # Detener después de 5 errores consecutivos


def run_worker(poll_interval: int = POLL_INTERVAL_SECONDS):
    """
    Inicia el worker que procesa tareas programadas.
    
    Args:
        poll_interval: Segundos entre cada revisión de tareas
    """
    logger.info("="*60)
    logger.info("🚀 INICIANDO TASK WORKER")
    logger.info("="*60)
    logger.info(f"Revisando tareas pendientes cada {poll_interval} segundos...")
    logger.info("")
    
    consecutive_errors = 0
    
    try:
        while True:
            try:
                # Obtener conexión a BD
                db = database.SessionLocal()
                
                # Obtener estadísticas
                stats = get_task_statistics(db)
                
                # Procesar tareas si hay pendientes
                if stats.get("pending_overdue", 0) > 0:
                    logger.info(f"⏳ Encontradas {stats['pending_overdue']} tareas vencidas. Procesando...")
                    
                    result = process_pending_tasks(db)
                    
                    logger.info(
                        f"✓ Procesadas: "
                        f"{result.get('successful', 0)} exitosas, "
                        f"{result.get('failed', 0)} fallidas"
                    )
                else:
                    logger.debug(
                        f"📊 Estado: "
                        f"total={stats.get('total_tasks', 0)}, "
                        f"ejecutadas={stats.get('executed', 0)}, "
                        f"pendientes={stats.get('pending_future', 0)}"
                    )
                
                db.close()
                consecutive_errors = 0  # Reset contador de errores
                
            except Exception as e:
                consecutive_errors += 1
                logger.error(
                    f"✗ Error procesando tareas ({consecutive_errors}/{MAX_CONSECUTIVE_ERRORS}): {str(e)}",
                    exc_info=True
                )
                
                if consecutive_errors >= MAX_CONSECUTIVE_ERRORS:
                    logger.critical(f"✗ {MAX_CONSECUTIVE_ERRORS} errores consecutivos. Deteniendo worker.")
                    raise
            
            # Esperar al siguiente ciclo
            time.sleep(poll_interval)
            
    except KeyboardInterrupt:
        logger.info("\n⏹️  Worker detenido por el usuario (Ctrl+C)")
    except Exception as e:
        logger.critical(f"✗ Error fatal en el worker: {str(e)}", exc_info=True)
        sys.exit(1)
    finally:
        logger.info("👋 Task Worker finalizado")


if __name__ == "__main__":
    # Parsear argumentos de línea de comandos
    poll_interval = POLL_INTERVAL_SECONDS
    
    if len(sys.argv) > 1:
        try:
            poll_interval = int(sys.argv[1])
            logger.info(f"Poll interval personalizado: {poll_interval} segundos")
        except ValueError:
            logger.warning(f"Argumento inválido: {sys.argv[1]}. Usando default: {POLL_INTERVAL_SECONDS}s")
    
    run_worker(poll_interval)
