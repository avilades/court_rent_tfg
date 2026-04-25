# Flujos de la Aplicación: Reserva de Pistas Deportivas

Este documento describe de forma detallada todos los flujos principales (casos de uso) que pueden ocurrir en la aplicación, detallando la interacción entre el Frontend (HTML), la API (Backend), la Base de Datos (BD) y los procesos secundarios.

---

## 1. Flujos de Usuario (Frontend)

### 1.1. Flujo de Registro de Usuario
**Objetivo:** Crear una nueva cuenta en el sistema.

1. **Frontend:** El usuario accede a la URL `/register`. El servidor (`app/main.py:register_page`) carga y devuelve la plantilla `register.html`.
2. **Acción:** El usuario rellena el formulario (Nombre, Apellidos, Email, Contraseña) y pulsa "Registrarse".
3. **API (Petición):** El navegador envía una petición `POST` a `/auth/register` con los datos en formato JSON.
4. **Backend (`app/routers/auth.py:register`):**
   * Invoca a `crud.get_user_by_email` para comprobar si el correo electrónico ya existe en la BD.
   * Si existe, devuelve un error HTTP 400.
   * Si no existe, invoca a `crud.create_user`.
5. **Base de Datos (`app/crud.py:create_user`):**
   * Encripta la contraseña (`get_password_hash`).
   * Crea un nuevo registro en la tabla `users`.
   * Crea un nuevo registro en la tabla `permissions` asocidado al usuario (activando `can_rent=True` y `is_admin=False`).
6. **Respuesta:** Devuelve el JSON del nuevo usuario creado.
7. **Frontend:** Muestra un mensaje de éxito y redirige a la página de inicio de sesión (`/`).

### 1.2. Flujo de Inicio de Sesión (Login)
**Objetivo:** Autenticarse en el sistema para acceder a funciones privadas.

1. **Frontend:** El usuario accede a `/` (raíz). El servidor (`app/main.py:home`) carga y devuelve la plantilla `login.html`.
2. **Acción:** El usuario introduce su email y contraseña, y pulsa "Iniciar sesión".
3. **API:** El formulario envía una petición `POST` tipo *OAuth2PasswordRequest* a `/auth/login`.
4. **Backend (`app/routers/auth.py:login`):**
   * Invoca a `crud.get_user_by_email` para buscar al usuario.
   * Invoca a `crud.verify_password` para comparar el hash guardado en BD con la contraseña recibida.
   * Si es correcto, genera un token JWT temporal (`create_access_token`) que incluye el email del usuario.
5. **Respuesta:** Devuelve un JSON con el token: `{"access_token": "...", "token_type": "bearer"}`.
6. **Frontend:** JavaScript guarda el token en el *LocalStorage* del navegador y redirige automáticamente al panel principal (`/dashboard`).

### 1.3. Flujo del Panel Principal (Dashboard)
**Objetivo:** Ver el área personal del jugador.

1. **Frontend:** El navegador es redirigido a `/dashboard`. El servidor (`app/main.py:dashboard`) renderiza `dashboard.html`.
2. **Acción:** La página carga e inmediatamente JavaScript ejecuta una petición `GET` a `/auth/me` con el token JWT en la cabecera (Authorization: Bearer <token>).
3. **API & Backend:** El middleware (`get_current_user`) decodifica el token, identifica al usuario y comprueba que esté activo. Verifica sus permisos y responde con los detalles de perfil.
4. **Frontend:** Muestra botones u opciones adaptados al rol (P.ej: botón de "Administración" solo si es admin).

### 1.4. Flujo de Consulta del Clima y Disponibilidad de Pistas
**Objetivo:** Ver qué pistas están libres en un día concreto y el pronóstico del tiempo.

1. **Frontend:** 
   * Usuario entra en "Reservar pista" y el servidor (`app/main.py:book_page`) devuelve `book.html`.
   * Selecciona una fecha (ej. `YYYY-MM-DD`) en el calendario interactivo.
2. **API (Clima):** 
   * JavaScript hace `GET /bookings/weather?date=YYYY-MM-DD`.
   * El Backend (`weather_service.py`) consulta la API de OpenWeatherMap, obtiene el pronóstico (Temperaturas, Lluvia/Nubes) y lo devuelve al frontend para mostrar sugerencias ("Día soleado, reserva exterior").
3. **API (Disponibilidad):** 
   * Al mismo tiempo, JS hace `GET /bookings/search?date=YYYY-MM-DD`.
   * El Backend (`app/routers/bookings.py:search_available_slots`) consulta la BD de la siguiente forma:
     * Consulta 1: Obtiene todas las pistas (`Court`) que no estén en mantenimiento.
     * Consulta 2: Obtiene todas las reservas activas (no canceladas) para ese día en `bookings`.
     * Consulta 3: Obtiene los horarios registrados para ese día de la semana en `schedules` para saber qué tipo de demanda (Alta, Media, Baja) se aplica cada hora.
     * Consulta 4: Obtiene el importe en vigor (`prices`) en esa fecha concreta según el nivel de demanda.
   * El backend cruza cruza los franjas (slots de 90min) en cada pista contra las reservas y descarta las ocupadas.
4. **Respuesta:** Lista JSON de "slots" disponibles (pista, fecha/hora inicio, fecha/hora fin, precio dinámico aplicable).
5. **Frontend:** Pinta una tabla visual o "cuadrante" con botones seleccionables de color azul donde esté libre.

### 1.5. Flujo de Creación de una Reserva (El "Core" del Sistema)
**Objetivo:** Alquilar una pista y recibir notificación.

1. **Acción:** En la página de reservas (tras elegir fecha y hora), el usuario hace clic en "Confirmar reserva".
2. **API:** JS envía un `POST /bookings/book` con el Payload (Fecha, Hora de inicio, ID de pista).
3. **Backend (`app/routers/bookings.py:book_court`):**
   * Comprueba permiso (`can_rent`).
   * Pasa los parámetros a la capa CRUD (`crud.create_booking`).
4. **Base de Datos (`app/crud.py:create_booking`):**
   * **Bloqueo/Concurrencia:** Comprueba si ese mismo slot está en `bookings` (si 2 personas clicaron a la vez). Si es así, aborta la transaccion con `None` (Conflict).
   * Genera el registro de la nueva reserva vinculando: user_id, court_id, horario y el *id del precio activo*.
   * Si ocurre un conflicto de Constraint única (Race condition), ejecuta un `rollback()`. Si funciona, hace un `commit()`.
5. **Procesos en Segundo Plano (Notificaciones):**
   * Invoca `generate_booking_confirmation_email` con la plantilla HTML.
   * Invoca `send_and_record_notification` y lanza un correo electrónico de forma diferida.
   * Invoca `schedule_reminder_task` insertando un registro en la tabla `scheduled_tasks` (programando aviso 24h antes del partido).
6. **Respuesta:** Se devuelve un 200 OK con los datos de la reserva, o un error 409 (Conflicto) si ya se ocupó.
7. **Frontend:** Muestra una notificación "SweetAlert" de éxito.

### 1.6. Flujo de Visualización de Mis Reservas
**Objetivo:** Consultar el histórico de reservas propias.

1. **Frontend:** El usuario hace clic en "Mis Reservas" (`/reservations`, plantilla `reservations.html`).
2. **API:** JS ejecuta `GET /bookings/my-bookings`.
3. **Backend (`app/routers/bookings.py` y `crud.py:get_user_bookings`):**
   * Obtiene la ID de usuario del JWT y consulta sus reservas en la tabla `Booking`, ordenado por el más reciente, y hace un `JOIN` a la tabla `prices` para saber el importe *exacto* que pagó por ella.
4. **Respuesta:** Array de reservas personales.

### 1.7. Flujo de Cancelación de Reserva
**Objetivo:** Abortar una reserva futura y recibir devolución.

1. **Acción:** En *Mis Reservas*, hace click en la (X) o botón de cancelar.
2. **API:** Se confirma en el navegador y lanza `POST /bookings/cancel/{booking_id}`.
3. **Backend (`app/routers/bookings.py:cancel_booking`):**
   * Localiza primero la reserva para verificar que es "dueño" de la misma.
   * Llama a `crud.cancel_booking_logic` para marcarla (cambia `is_cancelled = True`). No la borra físicamente para auditoria e histórico.
   * Llama a `generate_cancellation_email` para notificar del reintegro.
   * Busca e **Invalida (anula)** la alerta programada (24h) de esa reserva borrándola de `scheduled_tasks`.
4. **Respuesta:** OK 200. El frontend recarga la lista.

### 1.8. Flujo de Perfil de Usuario y Cambio de Contraseña
**Objetivo:** Actualizar los datos personales o cambiar la contraseña de acceso.

1. **Frontend:** El usuario accede a la sección de su Perfil desde el Dashboard (`/profile`, renderiza `profile.html`).
2. **API (Lectura):** JavaScript ejecuta una petición `GET /auth/me` (o al cargar la plantilla) para precargar los datos.
3. **Acción (Cambio de Contraseña):** El usuario teclea su contraseña actual, una nueva contraseña y la confirmación. Pulsa "Actualizar contraseña".
4. **API (Actualización):** El formulario o frontend envía una petición `PUT /auth/password` o `PUT /users/me/password` con el formato JSON necesario.
5. **Backend (`app/routers/auth.py` o `users.py`):**
   * Verifica la sesión mediante el token recibido.
   * Invoca a `crud.verify_password` para comprobar que la "contraseña actual" enviada coincide con la guardada en BD.
   * Si es incorrecta, devuelve error HTTP 400.
   * Si es correcta, genera un nuevo hash de la contraseña nueva (`get_password_hash`) e invoca `crud.update_password` para persistir los cambios en la tabla `users`.
6. **Respuesta:** JSON o HTTP 200 OK confirmando el cambio.
7. **Frontend:** Muestra una notificación de éxito y, por seguridad, puede pedir al usuario que vuelva a Iniciar Sesión eliminando el token.

---

## 2. Flujos de Administración (Solo usuarios Administradores)

### 2.1. Flujo de Modificación de Precios (Tarifas Dinámicas)
**Objetivo:** Alterar los precios vinculados a la demanda.

1. **Frontend:** El administrador visita el panel de precios (`/admin/precio`, plantilla `admin_precio.html`).
2. **API (Lectura):** Llama a `GET /admin/prices`. El backend (en router `/admin/prices`) revisa que es admin leyendo su JWT, hace ping a la BD en tabla `prices` donde `is_active=True` y las devuelve al frontal.
3. **Acción:** El admin escribe "15.00" para demanda Alta y pulsa Guardar. 
4. **API (Actualización):** Se llama a `POST /admin/prices/update`.
5. **Backend (`app/routers/admin.py:update_price`):**
   * Lógica de versionado (Soft-Delete/Audit):
   * Localiza el precio antiguo activo para ese tipo de demanda y le añade fecha de fin (`end_date = actual`) y la pone como `is_active = False`.
   * Inserta una ***nueva*** fila del precio con la cantidad nueva, manteniendo el hilo de trazabilidad.
6. A partir de aquí, las nuevas consultas de disponibilidad leerán solo el nuevo precio.

### 2.2. Flujo de Generación de Analíticas (Dashboard y KPIs)
**Objetivo:** Analizar ingresos, ocupación por pistas, y alertas.

1. **Frontend:** El administrador visita "Análiticas" (`/admin/stats`). Se abre la plantilla `admin_stats.html`.
2. **API:** Carga un script de gráficos que hace petición profunda `GET /admin/stats-data?period=30` (30 días).
3. **Backend (`app/routers/admin.py:get_stats`):**
   * Computación Agregada (OLAP ligero): 
     * **Total Ingresos**: `SUM()` del precio de las `bookings` (join tabla `prices`) no canceladas.
     * **Ocupación/Heatmap**: `COUNT()` agrupado (`GROUP BY`) por `court_id` y por la fecha extraída (`EXTRACT(hour)`).
     * **Top Jugadores**: `COUNT()` agrupado por `user_id`, limite de 5 filas y orden descenfente.
     * **Alertas**: Detecta infra-uso de pistas usando fórmulas.
4. **Respuesta:** JSON gigante estructurado por métricas (`{ total_income: X, occupancy_by_hour: {}, top_users: [] }`).
5. **Frontend:** JavaScript alimenta librerías (ej. Chart.js) renderizando gráficos circulares, barras, y líneas de tendencia.

### 2.3. Flujo de Cierre de Pista por Mantenimiento
**Objetivo:** Impedir temporalmente el alquiler de una pista rota.

1. **Frontend:** El encargado entra en su panel, va a la sección de Pistas y usa un interruptor ("en Mantenimiento").
2. **API:** Llama a `POST /admin/courts/{id}/maintenance`.
3. **Backend (`app/routers/admin.py:toggle_maintenance`):** Cambia el valor booleano `is_maintenance` en la tabla `courts` al contrario del que tenía.
4. A partir de ahora, cuando un jugador pida ver pistas de un dia, el `search_available_slots` la excluirá por completo de la matriz y saldrá en rojo.

### 2.4. Flujo de Gestión de Usuarios y Permisos
**Objetivo:** Consultar la base de usuarios, editar su perfil o suspender (banear) el acceso de jugadores.

1. **Frontend:** El administrador accede al apartado de Usuarios en su panel (`/admin/users`, renderiza `admin_users.html`).
2. **API (Lectura):** El frontend solicita `GET /admin/users` para traer la lista paginada o completa de cuentas registradas.
3. **Backend (`app/routers/admin.py:get_all_users`):**
   * Verifica que el rol sea de administrador basándose en el JWT actual.
   * Consulta a la capa `crud.get_users()` extrayendo datos y sus permisos desde la tabla de `users` y `permissions`.
4. **Respuesta:** JSON o tabla renderizada con los usuarios.
5. **Acción (Cambio de Estado/Password):** El administrador busca a un jugador concreto y, por ejemplo, lo inactiva pulsando un botón, o fuerza un reset de contraseña temporal.
6. **API (Modificación):** Lanza una petición `PATCH /admin/users/{user_id}/status`.
7. **Backend (`app/routers/admin.py:update_user_status`):**
   * Cambia el booleano `is_active=False` (o similar) en la BD.
   * La próxima vez que este usuario intente el Flujo de Inicio de sesión (1.2), el sistema lo rechazará en el chequeo de actividad.

---

## 3. Flujos en Segundo Plano (Workers / Cron Jobs)

### 3.1. Flujo de Scheduler Automático (Recordatorios de 24h)
**Objetivo:** Enviar emails programados al jugador.

1. **Componente de Inicio (`scheduler_service.py`):** Un hilo que se levanta bajo la interfaz al arrancar FastAPI (`startup_event` de main.py).
2. **Ejecución Periódica (`process_pending_tasks`):**
   * El servicio extra-hilo consulta constántemente la tabla `scheduled_tasks` buscando tareas pendientes cuyo contador `scheduled_for` (ej. 24h antes del partido) ya haya pasado o sea igual a la hora actual, y que `is_executed` sea Falso.
3. **Ejecutor:** 
   * Si la encuentra, genera un correo.
   * Envía por SMTP (SendGrid, Mailgun o cuenta Gmail).
4. **Resultado:** Marca la tarea con la fecha (`executed_at`), y pone `is_executed=True`. Si el servidor de correos cae, incrementa un `retry_count` hasta un tope para no morir infinitamente. Todo sin que el usuario que está navengando lo note.
