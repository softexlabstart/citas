# Sistema de Gestión de Citas

Este es un sistema de gestión de citas completo con un frontend en **React** y un backend en **Django**. Permite a los usuarios registrarse, iniciar sesión, ver servicios, consultar disponibilidad y gestionar sus citas. Incluye un panel de administración robusto y funcionalidades avanzadas como la generación de informes y roles de usuario diferenciados.

## Características

*   **Autenticación de Usuarios**: Registro e inicio de sesión con tokens JWT.
*   **Gestión de Múltiples Sedes**: El sistema está diseñado para operar con distintas sucursales o sedes.
*   **Gestión de Citas**: Los usuarios pueden agendar, reprogramar y cancelar citas.
*   **Visualización Avanzada**: Las citas se muestran en una tabla filtrable y en un calendario interactivo.
*   **Consulta de Disponibilidad**: Interfaz para consultar horarios disponibles por recurso y fecha, incluyendo la búsqueda de la próxima cita disponible para un servicio específico en una sede.
*   **Roles y Permisos**: Sistema de roles diferenciados (Usuario Regular, Administrador de Sede, Staff).
*   **Informes y Exportación**: Generación de informes de citas con filtros y opción de exportar a CSV.
*   **Notificaciones**: Notificaciones en la interfaz y por correo electrónico (confirmación y recordatorios).
*   **Internacionalización (i18n)**: Interfaz traducida al español.
*   **Panel de Administración**: Panel de Django para una gestión de bajo nivel de todos los modelos de datos.

## Roles y Permisos

El sistema define tres roles principales para controlar el acceso y las funcionalidades:

1.  **Usuario Regular**:
    *   Puede agendar nuevas citas para sí mismo.
    *   Puede ver, reprogramar y cancelar sus propias citas.
    *   Su visibilidad está limitada a su propia actividad.

2.  **Administrador de Sede**:
    *   Gestiona una o más sedes asignadas.
    *   Puede ver y administrar todas las citas, recursos y horarios de sus sedes.
    *   Tiene acceso a informes específicos de sus sedes.
    *   **No puede** agendar nuevas citas desde la interfaz de usuario regular; su rol es de gestión.

3.  **Staff / Superusuario**:
    *   Tiene control total sobre el sistema.
    *   Puede gestionar todas las sedes, usuarios, citas y configuraciones.
    *   Tiene acceso a todos los informes y funcionalidades administrativas.

## Documentación de la API

La API RESTful es el núcleo del backend. Todos los endpoints están prefijados con `/api/`.

### Autenticación
*   `POST /api/login/`: Iniciar sesión.
*   `POST /api/register/`: Registrar un nuevo usuario.
*   `POST /api/token/refresh/`: Refrescar el token de acceso.

### Citas
*   `GET /api/citas/citas/`: Obtener lista de citas (filtrada por rol).
*   `GET /api/citas/citas/?estado={estado}`: Filtrar citas por estado.
*   `POST /api/citas/citas/`: Crear una nueva cita.
*   `PATCH /api/citas/citas/{id}/`: Actualizar parcialmente una cita (ej. para reprogramar).
*   `DELETE /api/citas/citas/{id}/`: Cancelar una cita (cambia el estado a 'Cancelada').
*   `POST /api/citas/citas/{id}/confirmar/`: Confirmar una cita pendiente.
*   `GET /api/citas/next-availability/?servicio_id={id}&sede_id={id}`: Obtener los próximos horarios disponibles para un servicio en una sede.

### Configuración (Servicios, Recursos, Sedes)
*   `GET /api/citas/servicios/`: Obtener lista de servicios.
*   `GET /api/citas/recursos/`: Obtener lista de recursos.
*   `GET /api/organizacion/sedes/`: Obtener lista de sedes.
*   `GET /api/citas/disponibilidad/?fecha={YYYY-MM-DD}&recurso_id={id}`: Consultar horarios disponibles.

### Informes
*   **Endpoint:** `GET /api/citas/reports/appointments/`
*   **Descripción:** Genera un informe de citas en un rango de fechas.
*   **Parámetros:**
    *   `start_date` (requerido): Fecha de inicio (`YYYY-MM-DD`).
    *   `end_date` (requerido): Fecha de fin (`YYYY-MM-DD`).
    *   `servicio_id` (opcional): Filtrar por ID de servicio.
    *   `recurso_id` (opcional): Filtrar por ID de recurso.
    *   `export` (opcional): Si el valor es `csv`, la respuesta será un archivo CSV descargable. De lo contrario, será un resumen en JSON.
*   **Ejemplo (Exportar a CSV):**
    ```
    GET /api/citas/reports/appointments/?start_date=2025-01-01&end_date=2025-01-31&export=csv
    ```

## Funcionalidades Adicionales

### Campo `metadata` para Flexibilidad
*   Los modelos `Servicio` y `Recurso` incluyen un campo `metadata` (`JSONField`) en el backend.
*   **Propósito:** Permite almacenar datos adicionales específicos de una industria (ej. "color_tinte" para un servicio de peluquería) sin modificar la base de datos.
*   **Nota:** La gestión de este campo se realiza actualmente a través del panel de administración de Django.

### Notificaciones por Correo Electrónico
*   **Confirmación de Cita:** Se envía un correo al usuario al agendar una nueva cita.
*   **Recordatorios de Cita:** Un comando de Django (`send_reminders`) permite enviar recordatorios para las citas del día siguiente. Este comando debe ser automatizado (ej. con un cron job).
*   **Configuración:** Requiere configurar las variables de entorno del servidor SMTP en el archivo `.env` del backend.

## Tecnologías Utilizadas

### Frontend
- React
- TypeScript
- React Router
- React Bootstrap
- React Big Calendar
- i18next
- React Toastify
- Axios

### Backend
- Django
- Django REST Framework
- PostgreSQL (o la base de datos que se configure)
- Openpyxl (para exportar a Excel)
- ReportLab (para exportar a PDF)
- `django-cors-headers`
- `djangorestframework-simplejwt`

## Instalación y Configuración

### Prerrequisitos

- Node.js y npm
- Python y pip
- PostgreSQL (o la base de datos de su elección)

### Backend

1.  **Clona el repositorio**:

    ```bash
    git clone <URL-DEL-REPOSITORIO>
    cd proyecto-citas-/backend
    ```

2.  **Crea y activa un entorno virtual**:

    ```bash
    python -m venv venv
    source venv/bin/activate
    ```

3.  **Instala las dependencias**:

    ```bash
    pip install -r requirements.txt
    ```

4.  **Configura la base de datos**:

    -   Crea un archivo `.env` en la raíz del directorio `backend/` y configura tus variables de base de datos, correo electrónico y `SECRET_KEY`.
    -   Ajusta la configuración de `DATABASES` en `core/settings.py` si no usas variables de entorno.

5.  **Aplica las migraciones**:

    ```bash
    python manage.py migrate
    ```

6.  **Crea un superusuario**:

    ```bash
    python manage.py createsuperuser
    ```

7.  **Inicia el servidor de desarrollo**:

    ```bash
    python manage.py runserver
    ```

### Frontend

1.  **Navega al directorio del frontend**:

    ```bash
    cd ../frontend
    ```

2.  **Instala las dependencias**:

    ```bash
    npm install
    ```

3.  **Inicia el servidor de desarrollo**:

    ```bash
    npm start # La aplicación se abrirá en http://localhost:3001 por defecto
    ```

## Uso

-   Accede a la aplicación en `http://localhost:3001`.
-   Regístrate o inicia sesión para empezar a gestionar tus citas.
-   Accede al panel de administración en `http://127.0.0.1:8000/admin` para gestionar los datos de la aplicación.

## Casos de Uso

-   **Clínicas y consultorios médicos**: Para que los pacientes puedan agendar citas con los doctores.
-   **Salones de belleza y spas**: Para que los clientes puedan reservar servicios.
-   **Talleres mecánicos**: Para que los clientes puedan agendar citas para la revisión de sus vehículos.
-   **Cualquier negocio que requiera agendamiento de citas**.