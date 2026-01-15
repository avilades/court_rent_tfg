import sys
import os

# Añadir el directorio raíz al PYTHONPATH para que encuentre el módulo 'app'
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import engine
from app.models import Base

if __name__ == "__main__":
    # Confirmar acción antes de proceder
    print("Iniciando reseteo de la base de datos...")
    
    print("Eliminando todas las tablas existentes...")
    Base.metadata.drop_all(bind=engine)
    
    print("Recreando las tablas desde los modelos actuales...")
    Base.metadata.create_all(bind=engine)
    
    print("¡Reseteo completado con éxito!")
    print("Nota: Los datos iniciales se cargarán al iniciar el servidor de FastAPI.")
