import requests
import datetime

BASE_URL = "http://localhost:8000"

def get_token():
    res = requests.post(f"{BASE_URL}/auth/login", data={"username": "admin@example.com", "password": "admin000"})
    return res.json()["access_token"]

def get_prices(token, date_str):
    res = requests.get(f"{BASE_URL}/bookings/search?date={date_str}", headers={"Authorization": f"Bearer {token}"})
    return res.json()

def update_price(token, demand_id, amount, start_date):
    res = requests.post(f"{BASE_URL}/admin/prices/update", 
                         headers={"Authorization": f"Bearer {token}"},
                         json={"demand_id": demand_id, "amount": amount, "start_date": start_date})
    return res.json()

def verify():
    token = get_token()
    today = "2026-01-15"
    tomorrow = "2026-01-16"
    
    print(f"--- Verificando Precios para Hoy ({today}) ---")
    slots_today = get_prices(token, today)
    # Buscamos el precio de demanda 1 (Alta) a las 20:00 (que es demanda 1 en dia de diario)
    price_today = next(s["price_amount"] for s in slots_today if s["start_time"].endswith("20:00:00"))
    print(f"Precio hoy a las 20:00: {price_today}€")
    
    new_amount = price_today + 10.0
    print(f"\n--- Actualizando precio para Mañana ({tomorrow}) a {new_amount}€ ---")
    update_price(token, 1, new_amount, f"{tomorrow}T00:00:00")
    
    print(f"\n--- Verificando Precios para Mañana ({tomorrow}) ---")
    slots_tomorrow = get_prices(token, tomorrow)
    price_tomorrow = next(s["price_amount"] for s in slots_tomorrow if s["start_time"].endswith("20:00:00"))
    print(f"Precio mañana a las 20:00: {price_tomorrow}€")
    
    print(f"\n--- Verificando que Hoy ({today}) mantiene el precio anterior ---")
    slots_today_recheck = get_prices(token, today)
    price_today_recheck = next(s["price_amount"] for s in slots_today_recheck if s["start_time"].endswith("20:00:00"))
    print(f"Precio hoy a las 20:00 (recheck): {price_today_recheck}€")
    
    if price_today == price_today_recheck and price_tomorrow == new_amount:
        print("\n✅ VERIFICACIÓN EXITOSA: La lógica de precios dinámicos por fecha funciona correctamente.")
    else:
        print("\n❌ FALLO EN LA VERIFICACIÓN.")

if __name__ == "__main__":
    verify()
