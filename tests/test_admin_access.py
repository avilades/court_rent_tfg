import httpx
import pytest

BASE_URL = "http://localhost:8000"

def test_admin_access():
    client = httpx.Client(base_url=BASE_URL, timeout=30.0)
    
    print("Testing registration...")
    # 1. Register a regular user
    reg_data = {
        "name": "Regular",
        "surname": "User",
        "email": "regular@example.com",
        "password": "password123"
    }
    client.post("/auth/register", json=reg_data)

    print("Testing login as regular user...")
    # 2. Login as regular user
    login_data = {
        "username": "regular@example.com",
        "password": "password123"
    }
    response = client.post("/auth/login", data=login_data)
    assert response.status_code == 200
    reg_token = response.json()["access_token"]

    print("Checking /auth/me for regular user...")
    # 3. Check /auth/me for regular user
    response = client.get("/auth/me", headers={"Authorization": f"Bearer {reg_token}"})
    assert response.status_code == 200
    user_info = response.json()
    assert user_info["email"] == "regular@example.com"
    assert user_info["permissions"]["is_admin"] is False

    print("Testing admin API access as regular user (should be 403)...")
    # 4. Try admin API as regular user
    from datetime import datetime
    payload = {
        "demand_id": 1,
        "amount": 100.0,
        "start_date": datetime.utcnow().isoformat()
    }
    response = client.post("/admin/prices/update", 
                          json=payload,
                          headers={"Authorization": f"Bearer {reg_token}"})
    assert response.status_code == 403
    assert "No tienes permisos" in response.json()["detail"] or "Acceso denegado" in response.json()["detail"]

    print("Testing login as admin...")
    # 5. Login as admin
    admin_login_data = {
        "username": "admin@example.com",
        "password": "admin000"
    }
    response = client.post("/auth/login", data=admin_login_data)
    assert response.status_code == 200
    admin_token = response.json()["access_token"]

    print("Checking /auth/me for admin...")
    # 6. Check /auth/me for admin
    response = client.get("/auth/me", headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 200
    admin_info = response.json()
    assert admin_info["permissions"]["is_admin"] is True

    print("Testing admin API access as admin (should be 200)...")
    # 7. Try admin API as admin
    response = client.post("/admin/prices/update", 
                          json=payload,
                          headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 200
    print("All tests passed successfully!")

if __name__ == "__main__":
    test_admin_access()
    print("Tests passed!")
