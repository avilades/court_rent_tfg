"""
Script para testear el nuevo sistema de recordatorios.
Crea una tarea de prueba y verifica que se procesa correctamente.

Uso:
    python tests/test_task_system.py
"""

import os
import sys
from datetime import datetime, timedelta

# Agregar directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app.services.task_service import (
    schedule_reminder_task,
    process_pending_tasks,
    get_task_statistics,
    cancel_pending_task
)
from app import models


def test_task_creation():
    """Test 1: Crear una tarea de recordatorio"""
    print("\n" + "="*60)
    print("TEST 1: Crear una tarea de recordatorio")
    print("="*60)
    
    db = SessionLocal()
    
    try:
        # Calcular tiempo de la tarea (5 minutos desde ahora)
        now = datetime.utcnow()
        start_time = now + timedelta(minutes=5)
        
        # Crear tarea para 1 minuto from a hora (para que sea procesada rápido)
        success = schedule_reminder_task(
            db=db,
            booking_id=9999,
            user_id=1,
            recipient_email="test@example.com",
            court_number=1,
            start_time=start_time
        )
        
        if success:
            print("✓ Tarea creada exitosamente")
            
            # Verificar que está en la BD
            task = db.query(models.ScheduledTask).filter(
                models.ScheduledTask.booking_id == 9999
            ).first()
            
            if task:
                print(f"✓ Tarea guardada en BD: task_id={task.task_id}")
                print(f"  - task_type: {task.task_type}")
                print(f"  - scheduled_for: {task.scheduled_for}")
                print(f"  - is_executed: {task.is_executed}")
                return True
            else:
                print("✗ Tarea no se guardó en la BD")
                return False
        else:
            print("✗ Error creando tarea")
            return False
            
    except Exception as e:
        print(f"✗ Excepción: {str(e)}")
        return False
    finally:
        db.close()


def test_task_statistics():
    """Test 2: Ver estadísticas de tareas"""
    print("\n" + "="*60)
    print("TEST 2: Ver estadísticas de tareas")
    print("="*60)
    
    db = SessionLocal()
    
    try:
        stats = get_task_statistics(db)
        
        print("✓ Estadísticas obtenidas:")
        print(f"  - Total tareas: {stats.get('total_tasks', 0)}")
        print(f"  - Ejecutadas: {stats.get('executed', 0)}")
        print(f"  - Vencidas (pendientes): {stats.get('pending_overdue', 0)}")
        print(f"  - Pendientes (futuro): {stats.get('pending_future', 0)}")
        print(f"  - Fallidas: {stats.get('failed', 0)}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error obteniendo estadísticas: {str(e)}")
        return False
    finally:
        db.close()


def test_task_processing():
    """Test 3: Procesar tareas pendientes (si las hay)"""
    print("\n" + "="*60)
    print("TEST 3: Procesar tareas pendientes")
    print("="*60)
    
    db = SessionLocal()
    
    try:
        # Primero, mover la tarea de prueba a hace 1 minuto (para que se procese)
        task = db.query(models.ScheduledTask).filter(
            models.ScheduledTask.booking_id == 9999
        ).first()
        
        if task:
            task.scheduled_for = datetime.utcnow() - timedelta(seconds=30)
            db.commit()
            print(f"✓ Tarea movida al pasado para testing")
        
        # Procesar tareas
        result = process_pending_tasks(db)
        
        if result:
            print("✓ Tareas procesadas:")
            print(f"  - Totales procesadas: {result.get('total_processed', 0)}")
            print(f"  - Exitosas: {result.get('successful', 0)}")
            print(f"  - Fallidas: {result.get('failed', 0)}")
            print(f"  - Aún pendientes: {result.get('still_pending', 0)}")
            return True
        else:
            print("✓ No había tareas para procesar (normal)")
            return True
            
    except Exception as e:
        print(f"✗ Error procesando tareas: {str(e)}")
        return False
    finally:
        db.close()


def test_task_cancellation():
    """Test 4: Cancelar una tarea"""
    print("\n" + "="*60)
    print("TEST 4: Cancelar una tarea")
    print("="*60)
    
    db = SessionLocal()
    
    try:
        # Crear otra tarea de test
        success = schedule_reminder_task(
            db=db,
            booking_id=8888,
            user_id=1,
            recipient_email="test2@example.com",
            court_number=2,
            start_time=datetime.utcnow() + timedelta(hours=24)
        )
        
        if success:
            print("✓ Tarea de prueba creada para testing cancelación")
            
            # Cancelarla
            cancelled = cancel_pending_task(db, 8888)
            
            if cancelled:
                print("✓ Tarea cancelada exitosamente")
                
                # Verificar estado
                task = db.query(models.ScheduledTask).filter(
                    models.ScheduledTask.booking_id == 8888
                ).first()
                
                if task:
                    print(f"✓ Estado actualizado: is_executed={task.is_executed}")
                    return True
                else:
                    print("✗ Tarea desapareció de la BD")
                    return False
            else:
                print("✗ Error cancelando tarea")
                return False
        else:
            print("✗ Error creando tarea de test")
            return False
            
    except Exception as e:
        print(f"✗ Excepción: {str(e)}")
        return False
    finally:
        db.close()


def run_all_tests():
    """Ejecuta todos los tests"""
    print("\n" + "█"*60)
    print("█" + " "*58 + "█")
    print("█" + "  🧪 PRUEBAS DEL SISTEMA DE TAREAS".center(58) + "█")
    print("█" + " "*58 + "█")
    print("█"*60)
    
    results = []
    
    # Tests
    results.append(("Crear Tarea", test_task_creation()))
    results.append(("Ver Estadísticas", test_task_statistics()))
    results.append(("Procesar Tareas", test_task_processing()))
    results.append(("Cancelar Tarea", test_task_cancellation()))
    
    # Resumen
    print("\n" + "="*60)
    print("RESUMEN DE RESULTADOS")
    print("="*60)
    
    for test_name, passed in results:
        status = "✓ PASADO" if passed else "✗ FALLIDO"
        print(f"{status:12} - {test_name}")
    
    total_passed = sum(1 for _, p in results if p)
    total_tests = len(results)
    
    print(f"\nResultado: {total_passed}/{total_tests} tests pasados\n")
    
    if total_passed == total_tests:
        print("✓ ¡TODOS LOS TESTS PASARON! El sistema de tareas está funcionando.")
    else:
        print(f"⚠️  {total_tests - total_passed} test(s) fallaron.")


if __name__ == "__main__":
    run_all_tests()
