import sys
import os
from datetime import datetime, timedelta

# Añadir el directorio raíz al path para poder importar la app
sys.path.append(os.getcwd())

from app.weather_service import get_weather_prediction

def test_weather():
    print("--- Probando Servicio de Clima ---")
    
    # Caso 1: Fecha dentro de rango (mañana)
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    print(f"\nProbando fecha cercana (mañana: {tomorrow}):")
    result = get_weather_prediction(tomorrow)
    print(f"Resultado: {result}")

    # Caso 2: Fecha fuera de rango (en un mes)
    next_month = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
    print(f"\nProbando fecha lejana (dentro de 30 días: {next_month}):")
    result = get_weather_prediction(next_month)
    print(f"Resultado: {result}")

    # Caso 3: Simular error de API (con una clave inválida)
    print("\nSimulando error de API (Clave inválida):")
    os.environ["OPENWEATHER_API_KEY"] = "clave_falsa_123"
    # Recargar el módulo para que tome la nueva clave
    import importlib
    import app.weather_service
    importlib.reload(app.weather_service)
    
    result = app.weather_service.get_weather_prediction(tomorrow)
    print(f"Resultado (debe fallar y dar N/A o mock): {result}")

if __name__ == "__main__":
    test_weather()
