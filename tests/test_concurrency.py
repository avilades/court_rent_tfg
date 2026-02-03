import pytest
from app import crud, schemas, models
from app.database import session_local, engine
from app.initialize import initialize_demands, initialize_prices, initialize_courts, initialize_schedules
from datetime import datetime

# Setup DB for testing
models.Base.metadata.create_all(bind=engine)

def test_concurrency_constraint():
    """
    Intenta crear dos reservas idénticas y verifica que la segunda falle
    debido a la constraint de base de datos, no solo por la lógica de python.
    """
    db = session_local()
    
    # Inicializar datos maestros necesarios
    initialize_demands(db)
    initialize_prices(db)
    initialize_courts(db)
    initialize_schedules(db)
    
    # Datos de prueba
    # Datos de prueba
    user = crud.get_user_by_email(db, "admin@admin.com")
    if not user:
        user = crud.get_user_by_email(db, "test@concurrency.com")
        if not user:
            user = crud.create_user(db, schemas.UserCreate(
                name="Test", surname="User", email="test@concurrency.com", password="password"
            ))

    booking_data = schemas.BookingCreate(
        court_id=1,
        date="2030-01-01",
        time_slot="11:00"
    )

    # 1. Primera reserva (debería funcionar)
    print("Intento 1...")
    res1 = crud.create_booking(db, booking_data, user.user_id)
    if res1 is None:
        print("FALLO Intento 1: La reserva devolvió None (¿ya existe?). Intentando limpiar primero.")
        # Intentar limpiar si ya existe
        existing = db.query(models.Booking).filter(
            models.Booking.court_id == 1, 
            models.Booking.start_time == datetime(2030, 1, 1, 11, 0)
        ).first()
        if existing:
            print(f"Borrando reserva existente {existing.booking_id}...")
            db.delete(existing)
            db.commit()
            res1 = crud.create_booking(db, booking_data, user.user_id)
            
    assert res1 is not None, "La primera reserva falló incluso tras limpieza"

    # 2. Segunda reserva idéntica (debería fallar y devolver None)
    print("Intento 2 (debería fallar)...")
    res2 = crud.create_booking(db, booking_data, user.user_id)
    
    if res2 is None:
        print("ÉXITO: La segunda reserva fue rechazada correctamente.")
    else:
        print("FALLO: Se permitieron dos reservas idénticas.")
        
    assert res2 is None, "El sistema permitió reservas duplicadas"

    # Limpieza
    # crud.cancel_booking_logic(db, res1["booking_id"], user.user_id)
    db.close()

if __name__ == "__main__":
    test_concurrency_constraint()
