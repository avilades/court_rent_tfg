# manual de Usuario: Reserva de Pistas Deportivas

Este documento explica de forma sencilla qué hace el programa y cómo usarlo, sin utilizar términos técnicos compliados.

## 1. ¿Qué es esto?

Imagina una recepción virtual para un club deportivo. Este programa es una página web que permite a los jugadores reservar pistas de tenis o pádel desde su ordenador o móvil, y a los administradores gestionar el club de forma fácil.

## 2. Para los Jugadores (Usuarios)

### Registro e Inicio de Sesión
*   **Lo primero es identificarse**: Como en cualquier app, necesitas una cuenta. Puedes registrarte con tu nombre, correo y una contraseña.
*   **Seguridad**: El programa guarda tu contraseña de forma "secreta" (encriptada), así que nadie, ni siquiera los dueños del programa, pueden leerla.

### Panel Principal (Dashboard)
Una vez dentro, verás un panel de control personal.
*   **Tus Reservas**: Aquí aparece una lista de las pistas que has reservado.
*   **Estado**: Te dice si la reserva está confirmada o cancelada.

### Reservar una Pista
Esta es la función principal.
1.  **Eliges el día**: Un calendario te deja seleccionar cuándo quieres jugar.
2.  **Ves el tiempo**: ¡El programa es listo! Te muestra qué tiempo hará ese día (si lloverá, nevará o hará sol) para ayudarte a decidir. Si va a llover, te sugerirá reservar una pista cubierta.
3.  **Eliges la hora y la pista**:
    *   Verás un cuadrante con todas las horas disponibles.
    *   Si una casilla está en **azul**, ¡está libre! Haz clic para reservarla.
    *   Si está en **gris**, ya la ha cogido otra persona.
4.  **Precios inteligentes**: Verás que no todas las horas cuestan lo mismo. Jugar un fin de semana por la mañana puede ser más caro que un martes a mediodía. El programa calcula el precio automáticamente según la demanda.
5.  **Confirmación inmediata**: Al hacer clic, el sistema comprueba en milisegundos que nadie te haya quitado la pista y te muestra un mensaje de éxito.
6.  **Email y recordatorio**: Tras la reserva recibirás un email de confirmación y el sistema programará automáticamente un recordatorio para 24 horas antes de tu reserva (procesado por un worker que lee las tareas guardadas en la base de datos).

---

## 3. Para los dueños del Club (Administradores)

Hay una zona especial a la que solo puede entrar el "Jefe" (Administrador). Desde aquí se controla todo el negocio.

### Panel de Administración
*   **Visión Global**: Gráficos sencillos que te dicen cuánto dinero ha ganado el club hoy o este mes, y cuáles son las horas más solicitadas.

### Gestión de Precios
*   **Tú mandas**: Puedes decidir cuánto cuesta jugar. ¿Quieres subir el precio los sábados porque va mucha gente? Puedes hacerlo. ¿Quieres bajarlo los lunes para atraer jugadores? También.
*   **Historial**: El programa guarda un registro de todos los cambios de precio que has hecho.

### Gestión de Usuarios y Pistas
*   **Usuarios**: Puedes ver quién está registrado en tu club.
*   **Pistas**: Si una pista se rompe o necesita mantenimiento, puedes "cerrarla" en el programa para que nadie pueda reservarla hasta que esté arreglada.

---

## 4. ¿Qué ocurre "por detrás"? (Magia invisible)

Aunque no lo veas, el programa hace cosas importantes para que todo funcione bien:

*   **El Guardián de Reservas (Integridad de Datos)**: Imagina que dos personas intentan reservar la *misma* pista a la *misma* hora exacta. El programa tiene un "árbitro" muy estricto que solo deja pasar al primero que llega. Al segundo le avisará de que ya está ocupada. Es imposible que haya dos reservas solapadas.
*   **El Meteorólogo (Servicio de Clima)**: El programa se conecta a internet para consultar la previsión del tiempo real en la ubicación de las pistas.
*   **El Candado (Seguridad)**: Toda la información viaja protegida para que tus datos personales estén seguros.
*   **El Cartero (Notificaciones)**: Cuando creas o cancelas una reserva, el sistema envía emails (confirmación, cancelación) y programa recordatorios 24h antes. Un proceso en segundo plano (`task_worker.py`) lee las tareas en la base de datos y envía esos correos de forma fiable.

---

## Resumen

Es una herramienta completa para quitarte dolores de cabeza:
*   **Jugador**: "Quiero jugar, miro si hace bueno, reservo y listo."
---
## 5. Guía Técnica Completa: Los archivos del proyecto

Si abres la carpeta del programa, verás muchos archivos. Aquí te explicamos para qué sirve cada uno, como si fueran las piezas de un coche.

### 🧠 El Cerebro (Python / Backend)

Estos archivos se encargan de la lógica: pensar, calcular y decidir. Están en la carpeta `app/`.

*   **`main.py` (El Director)**: Es el punto de entrada. Arranca el servidor, enchufa todos los cables y dice "¡Acción!".
*   **`models.py` (Los Planos)**: Define cómo son los datos. Le dice a la base de datos: "Un Usuario tiene nombre, email y contraseña" o "Una Reserva tiene fecha, hora y precio".
*   **`schemas.py` (La Aduana)**: Verifica que los datos que entran y salen sean correctos. Si intentas registrarte sin email, este archivo te para los pies.
*   **`crud.py` (El Archivero)**: Son las siglas de *Create, Read, Update, Delete*. Este archivo es el único que toca la base de datos para guardar reservas, leer usuarios o borrar datos.
*   **`database.py` y `dependencies.py` (La Conexión)**:
    *   `database.py`: Abre el "túnel" hacia la base de datos.
    *   `dependencies.py`: Gestiona la seguridad, como verificar que tu "llave" (token) de sesión es válida.
*   **`weather_service.py` (El Meteorólogo)**: Se conecta a Internet (OpenWeatherMap) para preguntar qué tiempo hace.
*   **`routers/` (Las Ventanillas)**: Organiza las peticiones por temas:
    *   `auth.py`: Todo lo relacionado con entrar y registrarse.
    *   `bookings.py`: Todo lo relacionado con reservar pistas.
    *   `admin.py`: La zona privada del jefe.

### 🎨 La Cara (HTML y CSS / Frontend)

Es lo que tú ves en la pantalla.

*   **`templates/` (Las Plantillas HTML)**: Son los esqueletos de las páginas web.
    *   `base.html`: El molde común (cabecera, menú y pie de página). Todas las demás páginas se "rellenan" dentro de esta.
    *   `login.html`, `register.html`: Formularios de entrada.
    *   `book.html`: La página principal de reservas con el cuadrante.
    *   `dashboard.html`: Tu panel personal.
    *   `admin_*.html`: Las páginas de administración (gráficos, precios, etc.).
*   **`static/styles.css` (El Maquillaje)**: Define los colores, fuentes, sombras y espacios. Hace que la web se vea moderna y bonita en lugar de ser texto plano aburrido.

### 🗄️ La Memoria (SQL / Base de Datos)

Aquí es donde se guarda la información para siempre.

*   **`scripts_sql/`**: Instrucciones directas para la base de datos.
    *   `create_index.sql`: Crea la regla sagrada de "No admitir dos reservas iguales".
    *   `insert_*.sql`: Scripts para meter datos iniciales (precios base, pistas, etc.) si empezamos de cero.

### 🏗️ La Infraestructura (Docker)

*   **`Dockerfile`**: Es una receta de cocina que dice: "Coge un sistema Linux, instálale Python, copia mis archivos y arranca el programa". Permite que funcione igual en mi ordenador que en el tuyo.
*   **`docker-compose.yml`**: Es el jefe de obra. Dice: "Levanta un contenedor con el programa y otro con la base de datos, y conéctalos entre sí".

