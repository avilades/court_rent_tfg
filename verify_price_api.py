import requests
import sys

def verify_price_api():
    """
    Script de prueba para verificar que el endpoint de búsqueda de pistas 
    devuelve correctamente el importe de los precios.
    Presupone que el servidor está corriendo en local (identificado por base_url).
    """
    base_url = "http://127.0.0.1:8000"
    date = "2026-01-14" # Una fecha futura para la prueba
    
    try:
        # 1. Llamada al endpoint de búsqueda para una fecha concreta
        res = requests.get(f"{base_url}/bookings/search?date={date}")
        if res.status_code != 200:
            print(f"Error al llamar a /bookings/search: {res.status_code}")
            return False
            
        slots = res.json()
        if not slots:
            print("No se devolvieron slots. Verifica si los datos están inicializados en la DB.")
            return False
            
        # 2. Verificar que al menos algún slot contiene información de precio
        has_prices = any(slot.get('price_amount') is not None for slot in slots)
        if has_prices:
            print("Verificación exitosa: Los slots contienen el campo 'price_amount'.")
            # Imprimimos algunos ejemplos para verificar visualmente
            for slot in slots[:3]:
                print(f"  Pista {slot['court_id']} a las {slot['start_time']}: {slot['price_amount']}€")
            return True
        else:
            print("Fallo: Ninguno de los slots devueltos contiene 'price_amount'.")
            return False
            
    except Exception as e:
        print(f"Error de conexión: {e}. ¿Está el servidor ejecutándose?")
        return False

if __name__ == "__main__":
    if not verify_price_api():
        # Salimos con código de error si la verificación falla
        sys.exit(1)
