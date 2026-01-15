import urllib.request
import urllib.parse
import json

BASE_URL = "http://localhost:8000"

def make_request(url, method="GET", data=None, headers=None):
    if headers is None:
        headers = {}
    
    req_data = None
    if data:
        if headers.get("Content-Type") == "application/json":
            req_data = json.dumps(data).encode("utf-8")
        else:
            req_data = urllib.parse.urlencode(data).encode("utf-8")
            
    req = urllib.request.Request(url, data=req_data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8")
    except Exception as e:
        return 0, str(e)

def test_password_reset():
    # 1. Login as Admin
    print("Iniciando sesión como administrador...")
    login_data = {"username": "admin@example.com", "password": "admin000"}
    status, res = make_request(f"{BASE_URL}/auth/login", method="POST", data=login_data)
    
    if status != 200:
        print(f"Error al iniciar sesión como admin: {res}")
        return
    
    admin_token = res["access_token"]
    headers = {
        "Authorization": f"Bearer {admin_token}",
        "Content-Type": "application/json"
    }
    print("Sesión de administrador iniciada correctamente.")

    # 2. Register a new user
    print("\nRegistrando un nuevo usuario para prueba...")
    user_data = {
        "email": "testuser@example.com",
        "name": "Test",
        "surname": "User",
        "password": "oldpassword"
    }
    status, res = make_request(f"{BASE_URL}/auth/register", method="POST", data=user_data, headers={"Content-Type": "application/json"})
    
    if status != 200:
        if "ya está registrado" in str(res):
             print("El usuario ya existe, procediendo...")
        else:
            print(f"Error al registrar usuario (Status {status}): {res}")
            # return
    else:
        print("Usuario registrado correctamente.")

    # 3. Get user id
    print("\nObteniendo lista de usuarios...")
    status, users = make_request(f"{BASE_URL}/admin/users-list", method="GET", headers=headers)
    
    test_user = next((u for u in users if u["email"] == "testuser@example.com"), None)
    
    if not test_user:
        print("No se encontró el usuario de prueba en la lista.")
        return
    
    user_id = test_user["user_id"]
    print(f"Usuario encontrado: ID={user_id}")

    # 4. Reset password
    print(f"\nReseteando contraseña para el usuario ID={user_id}...")
    reset_data = {"user_id": user_id, "new_password": "newpassword123"}
    status, res = make_request(f"{BASE_URL}/admin/users/reset-password", method="POST", data=reset_data, headers=headers)
    
    if status == 200:
        print(f"Éxito: {res['msg']}")
    else:
        print(f"Error al resetear contraseña: {res}")
        return

    # 5. Verify new password
    print("\nVerificando inicio de sesión con la nueva contraseña...")
    login_data_new = {"username": "testuser@example.com", "password": "newpassword123"}
    # Note: /auth/login expects form data, so we don't set application/json header here
    status, res = make_request(f"{BASE_URL}/auth/login", method="POST", data=login_data_new)
    
    if status == 200:
        print("Éxito: Inicio de sesión correcto con la nueva contraseña.")
    else:
        print(f"Error: No se pudo iniciar sesión con la nueva contraseña (Status {status}): {res}")

if __name__ == "__main__":
    test_password_reset()
