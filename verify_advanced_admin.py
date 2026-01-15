import requests
import time

BASE_URL = "http://localhost:8000"

def get_token():
    res = requests.post(f"{BASE_URL}/auth/login", data={"username": "admin@example.com", "password": "admin000"})
    return res.json()["access_token"]

def test_stats(token):
    print("--- Verificando Estadísticas ---")
    headers = {"Authorization": f"Bearer {token}"}
    res = requests.get(f"{BASE_URL}/admin/stats-data", headers=headers)
    if res.status_code == 200:
        print("OK:", res.json())
    else:
        print("ERROR:", res.status_code, res.text)

def test_maintenance(token):
    print("\n--- Verificando Mantenimiento Pista 1 ---")
    headers = {"Authorization": f"Bearer {token}"}
    
    # 1. Poner en mantenimiento
    res = requests.post(f"{BASE_URL}/admin/courts/1/maintenance", headers=headers)
    print("Toggle ON:", res.json())
    
    # 2. Verificar que no aparece en búsqueda
    res = requests.get(f"{BASE_URL}/bookings/search?date=2026-01-15", headers=headers)
    slots = res.json()
    court_ids = set(s["court_id"] for s in slots)
    if 1 not in court_ids:
        print("Pista 1 correctamente oculta.")
    else:
        print("ERROR: Pista 1 sigue visible.")
        
    # 3. Quitar mantenimiento
    res = requests.post(f"{BASE_URL}/admin/courts/1/maintenance", headers=headers)
    print("Toggle OFF:", res.json())
    
    # 4. Verificar que vuelve a aparecer
    res = requests.get(f"{BASE_URL}/bookings/search?date=2026-01-15", headers=headers)
    slots = res.json()
    court_ids = set(s["court_id"] for s in slots)
    if 1 in court_ids:
        print("Pista 1 correctamente reactivada.")
    else:
        print("ERROR: Pista 1 no aparece.")

if __name__ == "__main__":
    try:
        token = get_token()
        test_stats(token)
        test_maintenance(token)
    except Exception as e:
        print("FALLO EN LA PRUEBA:", e)
