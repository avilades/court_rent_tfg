# Memoria del Proyecto Fin de Ciclo: CourtRent

**Título:** Sistema Multiplataforma para la Gestión y Reserva Automatizada de Pistas Deportivas con Integración Meteorológica y Precios Dinámicos.
**Autor:** [Tu Nombre]
**Ciclo:** Grado Superior en Desarrollo de Aplicaciones Multiplataforma (DAM)
**Fecha:** Marzo 2026

---

## RESUMEN (Abstract)

El presente proyecto consiste en el diseño e implementación de una aplicación web moderna para la gestión de alquiler de pistas deportivas (tenis y pádel). La plataforma, denominada **CourtRent**, utiliza un backend robusto basado en **FastAPI** y una base de datos relacional **PostgreSQL**, garantizando alta disponibilidad y concurrencia. Entre sus características innovadoras se incluye un motor de **precios dinámicos** que ajusta las tarifas según la demanda y una integración con servicios meteorológicos (**OpenWeatherMap**) para asesorar al usuario en su reserva. La seguridad se gestiona mediante tokens **JWT**, y el despliegue se facilita mediante la contenedorización con **Docker**.

**Palabras clave:** FastAPI, PostgreSQL, JWT, Docker, Reserva de pistas, Precios dinámicos, Web App.

---

## 1. INTRODUCCIÓN

### 1.1. Contexto y Motivación
En la actualidad, la digitalización de los centros deportivos es una necesidad imperativa para mejorar la experiencia del usuario y optimizar la gestión administrativa. Muchos clubes aún dependen de sistemas arcaicos o procesos manuales que generan conflictos de horario y falta de transparencia en los precios.

### 1.2. Objetivos
El objetivo principal es desarrollar una solución integral que automatice el ciclo de vida de una reserva deportiva, desde el registro del usuario hasta la confirmación y recordatorio por correo electrónico.

**Objetivos Específicos:**
*   Implementar una API REST eficiente con FastAPI.
*   Desarrollar un sistema de autenticación seguro basado en arquitectura moderna.
*   Diseñar un algoritmo de precios que maximice la rentabilidad del club (Demand-based pricing).
*   Integrar avisos meteorológicos en tiempo real para reducir cancelaciones por mal tiempo.
*   Proveer un panel de analíticas para la toma de decisiones basada en datos (Business Intelligence).

### 1.3. Alcance
La aplicación cubre la gestión de usuarios, visualización de disponibilidad en cuadrantes horarios de 90 minutos, sistema de pagos simulado, cancelaciones automáticas y un módulo administrativo completo para la configuración del club.

---

## 2. ANÁLISIS DE TECNOLOGÍAS (Estado del Arte)

Para el desarrollo de **CourtRent**, se han seleccionado tecnologías de vanguardia que aseguran rendimiento y mantenibilidad:

*   **Python (FastAPI):** Elegido por su rapidez de ejecución y su soporte nativo para programación asíncrona, fundamental para manejar múltiples peticiones de reserva simultáneas.
*   **PostgreSQL:** Como motor de base de datos relacional robusto, esencial para mantener la integridad referencial (evitar "double bookings").
*   **SQLAlchemy:** ORM (Object-Relational Mapping) para una gestión de datos orientada a objetos.
*   **JWT (JSON Web Tokens):** Estándar industrial para la autenticación sin estado en aplicaciones modernas.
*   **Jinja2 & CSS:** Suite de herramientas para un frontend dinámico y visualmente atractivo (Premium Aesthetics).
*   **Docker:** Para garantizar que el entorno de desarrollo sea idéntico al de producción.

---

[Continuará con Diseño de Sistema e Implementación...]

---

## 3. DISEÑO DEL SISTEMA

### 3.1. Arquitectura de la Aplicación
El sistema sigue una arquitectura de **Capas** para separar las responsabilidades y facilitar el mantenimiento:
1.  **Capa de Presentación (Frontend):** Desarrollada con plantillas **Jinja2** y **Vanilla CSS**, proporcionando una interfaz reactiva y moderna.
2.  **Capa de Aplicación (API REST):** Construida con **FastAPI**, gestiona la lógica de negocio, validación de esquemas (Pydantic) y seguridad.
3.  **Capa de Datos (Persistencia):** Utiliza **PostgreSQL** mediante el ORM **SQLAlchemy**, asegurando transacciones seguras.
4.  **Capa de Servicios de Terceros:** Integración con **OpenWeatherMap** para datos climáticos y servidores **SMTP** para notificaciones.

### 3.2. Diseño de la Base de Datos (Modelo Entidad-Relación)
El corazón de **CourtRent** es su esquema relacional, diseñado para evitar conflictos de reserva y mantener la integridad histórica.

#### 3.2.1. Entidades Principales:
*   **User & Permission:** Relación 1:1 que separa los datos de perfil de los privilegios de acceso (Admin, CanRent, etc.).
*   **Court:** Representa las 8 pistas físicas. Incluye estados de mantenimiento.
*   **Booking (La Reserva):** La entidad central. Utiliza una **restricción de unicidad parcial (Partial Unique Index)** en PostgreSQL para garantizar que no existan dos reservas activas para la misma pista y hora, ignorando las canceladas.
*   **Price (Precios Dinámicos):** Implementa un sistema de **versionado**. Cada reserva guarda un `price_id` (snapshot), de modo que si el administrador cambia el precio del fin de semana hoy, las reservas realizadas ayer mantienen su precio original en el historial.
*   **Schedule & Demand:** Vinculan los bloques horarios con niveles de demanda (Alta, Media, Baja), permitiendo que el sistema calcule el precio automáticamente según el día y la hora.

#### 3.2.2. Sistema de Tareas y Notificaciones:
*   **ScheduledTask:** Tabla que actúa como cola de tareas persistente. Un worker independiente procesa estos registros para enviar recordatorios 24 horas antes de la reserva.
*   **Notification:** Registro de auditoría de todos los correos enviados (Confirmación, Cancelación, Recordatorio).

---

## 4. IMPLEMENTACIÓN TÉCNICA

### 4.1. Seguridad y Autenticación
Se ha implementado un sistema de autenticación basado en **OAuth2 con JWT**.
1.  El usuario envía credenciales.
2.  El servidor valida el hash de la contraseña (usando `passlib`).
3.  Se genera un Token firmado con una `SECRET_KEY`.
4.  El cliente incluye este token en las cabeceras de cada petición protegida.

### 4.2. Lógica de Reserva y Precios
Cuando un usuario consulta una fecha, el sistema realiza los siguientes pasos:
1.  Obtiene la previsión meteorológica para ese día.
2.  Cruza el calendario con los slots de `Schedule` para determinar el nivel de demanda.
3.  Busca el `Price` activo para dicha demanda.
4.  Verifica la disponibilidad física de las pistas en `Booking`.
