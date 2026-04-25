# Reserva de Pista - Proyecto Python

## Descripción
Este proyecto es una aplicación web para gestionar reservas de pistas deportivas. Utiliza **FastAPI** para la API, **SQLAlchemy** para la base de datos, y **HTML/JavaScript** para la interfaz de usuario. Incluye funcionalidades para:
- Gestionar usuarios y permisos
- Reservar y cancelar pistas
- Notificaciones automáticas
- Estadísticas y gráficos
- Trabajo en segundo plano para recordatorios

## Características
- ✅ API REST con FastAPI
- 🗓️ Sistema de reservas con notificaciones
- 📊 Estadísticas en tiempo real
- 🧼 Plantillas HTML con Bootstrap
- 🔄 Worker para tareas programadas
- 🌍 Integración con servicios meteorológicos

## Tecnologías
- Python 3.14
- FastAPI
- SQLAlchemy (PostgreSQL/SQLite)
- Jinja2 para plantillas
- Celery (para tareas asincrónicas)
- Chart.js para gráficos
- dotenv para variables de entorno

## Instalación
1. Clona el repositorio
2. Crea un entorno virtual:
   ```bash
   python3 -m venv venv
   source venv/bin/activate