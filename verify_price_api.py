import requests
import sys

def verify_price_api():
    base_url = "http://127.0.0.1:8000"
    date = "2026-01-14" # A future date
    
    try:
        # Check search endpoint
        res = requests.get(f"{base_url}/bookings/search?date={date}")
        if res.status_code != 200:
            print(f"Error calling /bookings/search: {res.status_code}")
            return False
            
        slots = res.json()
        if not slots:
            print("No slots returned. Check if data is initialized.")
            return False
            
        has_prices = any(slot.get('price_amount') is not None for slot in slots)
        if has_prices:
            print("Successfully verified: Slots contain price_amount.")
            # Print a few examples
            for slot in slots[:3]:
                print(f"  Court {slot['court_id']} at {slot['start_time']}: {slot['price_amount']}€")
            return True
        else:
            print("Failure: No slots contain price_amount.")
            return False
            
    except Exception as e:
        print(f"Connection error: {e}. Is the server running?")
        return False

if __name__ == "__main__":
    if not verify_price_api():
        sys.exit(1)
