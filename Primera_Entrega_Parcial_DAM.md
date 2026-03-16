# Primera Entrega Parcial: Proyecto Intermodular (DAM)

**Nombre del Proyecto:** Plataforma de Reserva de Pistas Deportivas ("Court Rent")
**Fase:** Desarrollo inicial (50% del trabajo total)

Este documento refleja la evolución del proyecto desde su idea inicial (anteproyecto) hacia un desarrollo estructurado, detallando la estructura arquitectónica, el esquema de la memoria, la alineación con el grado superior y sus objetivos definitivos.

---

## 1. Estructura General del Proyecto

La aplicación ha pasado de una arquitectura conceptual a una implementación técnica real basada en un entorno cliente-servidor, con el backend separado en capas lógicas y el frontend consumiendo estos servicios a través de renderizado del lado del servidor.

### Pila Tecnológica
- **Backend / API REST:** Python 3 con FastAPI.
- **Base de Datos:** PostgreSQL (orm gestionado a través de SQLAlchemy).
- **Frontend:** HTML5, CSS3 puro y un sistema de renderizado de plantillas con Jinja2.
- **Entorno de Desarrollo / Despliegue:** Docker, Docker Compose y Devcontainers.

### Organización del Repositorio
La estructura de archivos refleja un patrón de diseño Modelo-Vista-Controlador (MVC) adaptado a FastAPI:

- `app/` *(Núcleo del servidor)*
  - `models.py`: Modelos relacionales de Base de Datos (SQLAlchemy).
  - `schemas.py`: Esquemas de validación y tipado de datos Pydantic (contratos de API).
  - `crud.py`: Capa de persistencia (Create, Read, Update, Delete).
  - `routers/`: Controladores divididos por dominio (`auth.py`, `bookings.py`, `admin.py`).
  - `templates/` y `static/`: Vistas HTML (Jinja2) y hojas de estilo CSS (Backend SSR).
  - `weather_service.py` / `task_service.py`: Servicios de terceros y tareas secundarias.
- `scripts_sql/`: Scripts de inicialización, definición de datos semilla e índices para evitar solapamientos.
- `docker-compose.yml` y `Dockerfile`: Orquestación del servicio web y el motor de la base de datos PostgreSQL.

---

## 2. Apartados Principales de la Memoria

La memoria final del proyecto seguirá una estructura académica técnica basada en normas estándar (como APA), que contendrá los siguientes apartados principales:

1. **Introducción y Justificación:** Planteamiento del problema (la necesidad física de digitalizar las reservas de un club), motivación y alcance del proyecto.
2. **Objetivos del Proyecto:** Generales y específicos (se detallan en la sección 4 de este documento).
3. **Análisis de Sistema y Requisitos:** 
   - Requisitos Funcionales y No Funcionales.
   - Casos de Uso del sistema (Usuarios, Administradores, Tareas de fondo).
4. **Diseño de la Aplicación:**
   - **Arquitectura del software:** Descripción del modelo Cliente-Servidor y API REST.
   - **Diseño de Base de Datos:** Modelo Entidad-Relación (E-R) y Modelo Relacional.
   - **Diseño de Interfaz (UI/UX):** Wireframes y diseño de navegación.
5. **Tecnologías, Herramientas y Entorno:** Justificación técnica tecnológica (FastAPI, Postgres, Docker).
6. **Implementación y Desarrollo:** Desarrollo de la lógica de negocio, endpoints, servicios integrados (Clima, Email) y securización JWT (JSON Web Tokens).
7. **Pruebas y Validación:** Testeo de integridad en bases de datos y control de concurrencia.
8. **Manuales:** Manual de Despliegue (Instalación) y Manual de Usuario.
9. **Conclusiones y Trabajo Futuro:** Valoración personal, logros y vías de ampliación.

---

## 3. Relación del Proyecto con los Módulos Profesionales (DAM)

El proyecto engloba y aplica de manera cruzada los conocimientos de los principales módulos del ciclo de Formación Profesional (DAM):

*   **Acceso a Datos (AD):** 
    *   Diseño y modelado relacional en PostgreSQL. 
    *   Mapeamiento Objeto-Relacional (ORM) mediante SQLAlchemy y validación de entidades (Crud).
    *   Manejo de transacciones para garantizar las propiedades ACID en la concurrencia de reservas.
*   **Desarrollo de Interfaces (DI):** 
    *   Diseño del panel frontend responsivo usando HTML5 y CSS3 usando Jinja2.
    *   Experiencia de usuario con menús de administración, cuadros de reserva interactivos y vistas dinámicas basadas en el rol.
*   **Programación de Servicios y Procesos (PSP):** 
    *   Desarrollo de una API asíncrona eficiente utilizando FastAPI.
    *   Implementación de procesos en segundo plano para notificaciones automáticas (`task_worker.py`).
    *   Comunicación e integración de servicios de red externos (API REST OpenWeatherMap).
*   **Sistemas de Gestión Empresarial (SGE):** 
    *   Creación de un módulo de gestión tipo ERP enfocado al club: gestión de usuarios, asignación de precios basada en demanda, bloqueo de pistas en mantenimiento y un panel de analíticas/estadísticas para toma de decisiones (Business Intelligence básico).
*   **Entornos de Desarrollo (ED):** 
    *   Flujo de control de versiones con Git (y uso de repositorio central).
    *   Virtualización y despliegue usando contenedores Docker (Devcontainers). 
    *   Documentación exhaustiva y formateo de código.

---

## 4. Objetivos Concretos y Definidos

Respecto al anteproyecto, los objetivos han pasado de intenciones abstractas a características técnicas específicas y medibles:

**Objetivo Principal:**
Desarrollar, empaquetar y desplegar un sistema integral web "fullstack" y multiplataforma, administrable y seguro para reservar pistas deportivas en tiempo real.

**Objetivos Específicos:**
1.  **Motor Asíncrono de Reservas:** Programar un algoritmo que permita la comprobación y cierre de reservas evadiendo condiciones de carrera y solapamiento de horarios en la base de datos (con índices de unicidad).
2.  **Sistema de Tarifas Dinámico:** Implementar un modelo de datos `Price > Demand > Schedule` que permita asignar precios diferentes según la demanda del horario (alta, media o baja) permitiendo la fluidez financiera del club deportivo.
3.  **Integración de Servicios Contextuales (Clima):** Consumir la API de OpenWeatherMap al momento de la reserva para informar al usuario de las previsiones meteorológicas del día exacto que desea jugar antes de confirmar la reserva.
4.  **Sistema de Notificaciones Diferidas:** Crear una rutina que persista "tareas" en base de datos para ejecutar un Worker asíncrono que mande correos de recordamiento puntualmente 24 horas antes del partido.
5.  **Panel de Administración y Analítica:** Construir un "Dashboard" restringido en el que los dueños puedan revisar el estado del club, cambiar precios en vivo, cerrar pistas para mantenimiento y observar cuadros de métricas (Ingresos mensuales, Ocupación).
6.  **Despliegue Contenerizado Automático:** Facilitar que el proyecto sea arrancable por un tercero en cualquier máquina en menos de 5 minutos utilizando un `docker-compose.yml` preconfigurado.
