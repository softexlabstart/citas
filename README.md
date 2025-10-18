# Sistema de Gestión de Citas Multi-Tenant

Sistema completo de gestión de citas con frontend en **React** y backend en **Django**, diseñado para soportar múltiples organizaciones independientes en una misma plataforma.

## Características Principales

- **Multi-Tenant**: Múltiples organizaciones con datos completamente aislados
- **Gestión de Múltiples Sedes**: Cada organización puede tener varias sucursales
- **Roles y Permisos**: Sistema de roles diferenciados (Cliente, Colaborador, Admin de Sede, Superusuario)
- **Autenticación JWT**: Registro e inicio de sesión seguro con tokens
- **Registro por Organización**: Cada organización tiene su URL de registro personalizada
- **Gestión de Citas**: Agendar, reprogramar, confirmar y cancelar citas
- **Disponibilidad Inteligente**: Consulta de horarios disponibles y próxima cita disponible
- **Visualización Avanzada**: Vista de tabla filtrable y calendario interactivo
- **Informes y Reportes**: Generación con filtros avanzados y exportación a CSV
- **Emails Asíncronos**: Envío de notificaciones mediante Celery
- **Notificaciones**: Confirmación, recordatorios y reprogramación por email
- **Reservas Anónimas**: Permite agendar sin registro previo
- **Dashboard Financiero**: Métricas y gráficos en tiempo real con Recharts
- **Internacionalización**: Interfaz en español con soporte i18n
- **Alta Concurrencia**: Optimizado con Redis, throttling y query optimization

## Tecnologías

### Frontend
- React + TypeScript
- React Router, React Bootstrap
- React Big Calendar, Recharts
- i18next, Axios, React Toastify

### Backend
- Django + Django REST Framework
- PostgreSQL
- Redis (caché y Celery broker)
- Celery (tareas asíncronas)
- JWT Authentication
- Gunicorn (WSGI server)

## Documentación

### 📚 Guías Principales
- **[Manual de Usuario](docs/MANUAL_DE_USO.md)** - Guía completa de uso para todos los roles
- **[Configuración de Producción](docs/DEPLOYMENT_GUIDE.md)** - Despliegue y optimizaciones
- **[Configuración de Celery + Redis](CELERY_SETUP.md)** - Emails asíncronos y workers

### 🔧 Documentación Técnica
- **[Arquitectura Multi-Tenant](docs/MULTITENANCY.md)** - Cómo funciona el aislamiento de datos
- **[Roles y Permisos](docs/ROLES_Y_PERMISOS.md)** - Sistema de autorizaciones
- **[Registro por Organización](docs/REGISTRO_ORGANIZACION.md)** - URLs personalizadas de registro
- **[Seguridad](docs/SECURITY_CHECKLIST.md)** - Checklist para producción

### 📊 Optimizaciones
- **[Resumen de Optimizaciones](docs/OPTIMIZATIONS.md)** - Performance y concurrencia

## Instalación Rápida

### Prerrequisitos
- Python 3.8+
- Node.js 14+
- PostgreSQL
- Redis

### Backend

```bash
# Clonar repositorio
git clone <URL-DEL-REPOSITORIO>
cd proyecto-citas-/backend

# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Configurar .env
cp .env.example .env
# Editar .env con tus credenciales

# Aplicar migraciones
python manage.py migrate

# Crear superusuario
python manage.py createsuperuser

# Iniciar servidor
python manage.py runserver
```

### Frontend

```bash
cd ../frontend

# Instalar dependencias
npm install

# Iniciar servidor de desarrollo
npm start
```

La aplicación estará disponible en `http://localhost:3001`

## Servicios Adicionales

### Redis (requerido para caché y Celery)

```bash
# Ubuntu/Debian
sudo apt install redis-server
sudo systemctl start redis-server

# macOS
brew install redis
brew services start redis

# OpenSUSE (ver CELERY_SETUP.md para más detalles)
sudo zypper install redis
sudo systemctl start redis-server
```

### Celery Worker (para emails asíncronos)

```bash
cd backend
celery -A core worker --loglevel=info
```

**Para producción**, ver [CELERY_SETUP.md](CELERY_SETUP.md) para configurar como servicio systemd.

## Uso Básico

### Crear una Organización

Como superusuario en Django Admin (`/admin`):
1. Ir a "Organizaciones"
2. Crear nueva organización (el slug se genera automáticamente)
3. Crear sedes para esa organización

### Registrar Usuarios por Organización

Cada organización tiene su URL de registro personalizada:
```
http://tu-dominio.com/register/{slug-organizacion}
```

Ejemplo:
```
http://localhost:3001/register/clinica-abc
```

Los usuarios que se registren con este link se asociarán automáticamente a "Clínica ABC".

### Roles de Usuario

| Rol | Descripción | Permisos |
|-----|-------------|----------|
| **Cliente** | Usuario final | Agendar sus propias citas, ver su historial |
| **Colaborador** | Profesional que ofrece servicios | Ver sus citas asignadas, crear citas para clientes |
| **Admin de Sede** | Gerente de sucursal | Gestionar citas, servicios y colaboradores de sus sedes |
| **Superusuario** | Admin del sistema | Acceso total, gestiona todas las organizaciones |

Ver [docs/ROLES_Y_PERMISOS.md](docs/ROLES_Y_PERMISOS.md) para más detalles.

## Configuración de Producción

### 1. Instalar Redis (si no está instalado)

```bash
bash install_redis.sh
```

### 2. Configurar Celery Worker

```bash
bash setup_celery.sh
```

### 3. Variables de Entorno

Configurar `.env` en el backend:

```env
DEBUG=False
SECRET_KEY=tu-clave-secreta-muy-larga
DB_NAME=citas_prod
DB_USER=citas_user
DB_PASSWORD=contraseña-segura
EMAIL_HOST=smtp.gmail.com
EMAIL_HOST_USER=tu-email@gmail.com
EMAIL_HOST_PASSWORD=tu-contraseña-de-app
FRONTEND_URL=https://tu-dominio.com
```

### 4. Configurar Gunicorn

```bash
cd backend
gunicorn --config gunicorn_config.py core.wsgi:application
```

### 5. Build del Frontend

```bash
cd frontend
npm run build
```

Ver [docs/DEPLOYMENT_GUIDE.md](docs/DEPLOYMENT_GUIDE.md) para configuración completa de Nginx, SSL y más.

## API Endpoints Principales

### Autenticación
- `POST /api/login/` - Iniciar sesión
- `POST /api/register/{slug}/` - Registro por organización
- `POST /api/token/refresh/` - Refrescar token

### Citas
- `GET /api/citas/citas/` - Listar citas (filtradas por rol)
- `POST /api/citas/citas/` - Crear cita
- `PATCH /api/citas/citas/{id}/` - Actualizar cita
- `DELETE /api/citas/citas/{id}/` - Cancelar cita
- `POST /api/citas/citas/{id}/confirmar/` - Confirmar cita

### Disponibilidad
- `GET /api/citas/disponibilidad/?fecha={YYYY-MM-DD}&recurso_id={id}` - Horarios disponibles
- `GET /api/citas/next-availability/?servicio_id={id}&sede_id={id}` - Próxima cita disponible

### Servicios y Recursos
- `GET /api/citas/servicios/` - Listar servicios
- `GET /api/citas/recursos/` - Listar colaboradores

### Informes
- `GET /api/citas/reports/appointments/?start_date={YYYY-MM-DD}&end_date={YYYY-MM-DD}&export=csv` - Exportar informe

## Casos de Uso

- **Clínicas y Consultorios Médicos**: Pacientes agendando citas con doctores
- **Salones de Belleza y Spas**: Clientes reservando servicios de estética
- **Talleres Mecánicos**: Clientes agendando revisiones de vehículos
- **Cualquier negocio con citas**: Sistema flexible y personalizable

## Optimizaciones Implementadas

### Performance
- **Rate Limiting**: 100 req/h anónimos, 1000 req/h autenticados
- **Redis Cache**: Servicios y recursos cacheados (5 min)
- **Query Optimization**: `select_related` y `prefetch_related` para evitar N+1
- **Database Indexes**: Índices en campos frecuentes
- **Gunicorn con Gevent**: Workers optimizados para I/O

### Seguridad
- **Django-Axes**: Bloqueo después de 5 intentos fallidos
- **CORS**: Origins específicos (no wildcard)
- **CSP Headers**: Content Security Policy
- **Validación de Contraseñas**: 4 validadores activos
- **JWT Tokens**: Access + Refresh tokens

### Asíncrono
- **Celery**: Envío de emails sin bloquear requests
- **Redis Broker**: Cola de tareas con DB 2
- **Auto-reintentos**: 3 intentos con 60s de delay

## Comandos Útiles

### Backend

```bash
# Aplicar migraciones
python manage.py migrate

# Crear superusuario
python manage.py createsuperuser

# Ejecutar tests
python manage.py test

# Enviar recordatorios (cron job)
python manage.py send_reminders

# Verificar deployment
python manage.py check --deploy
```

### Frontend

```bash
# Desarrollo
npm start

# Build para producción
npm run build

# Linting
npm run lint
```

### Celery

```bash
# Iniciar worker
celery -A core worker --loglevel=info

# Ver estado
celery -A core inspect stats

# Monitorear tareas
celery -A core events
```

### Redis

```bash
# Verificar conexión
redis-cli ping  # Debe responder: PONG

# Ver estadísticas
redis-cli INFO stats

# Limpiar cache
redis-cli FLUSHDB
```

## Monitoreo

### Ver Logs

```bash
# Gunicorn
sudo journalctl -u gunicorn -f

# Celery
sudo journalctl -u celery -f
tail -f /var/log/celery/worker.log

# Nginx
sudo tail -f /var/log/nginx/error.log
sudo tail -f /var/log/nginx/access.log
```

### Estado de Servicios

```bash
# Backend
sudo systemctl status gunicorn

# Celery
sudo systemctl status celery

# Redis
sudo systemctl status redis-server  # o redis6, redis@redis

# Nginx
sudo systemctl status nginx
```

## Troubleshooting

### Problema: Emails no se envían

**Verificar:**
1. Celery worker está corriendo: `sudo systemctl status celery`
2. Redis está activo: `redis-cli ping`
3. Logs de Celery: `tail -f /var/log/celery/worker.log`
4. Configuración SMTP en `.env`

**Solución:**
```bash
sudo systemctl restart celery
```

### Problema: Worker timeout en Gunicorn

**Causa**: Query muy pesado en endpoint

**Solución**: Ver [docs/OPTIMIZATIONS.md](docs/OPTIMIZATIONS.md) para optimizaciones de queries

### Problema: Organización no encontrada al registrar

**Verificar:**
1. Slug de la organización existe en DB
2. URL es correcta: `/register/{slug-exacto}`
3. Endpoint: `GET /api/organizacion/organizaciones/{slug}/`

## Licencia

[Especificar licencia]

## Contribuidores

[Lista de contribuidores]

## Soporte

Para reportar problemas o solicitar ayuda:
- **Issues**: [GitHub Issues](link-al-repo)
- **Documentación**: Ver carpeta `docs/`
- **Email**: [email de soporte]

---

**Versión:** 2.0
**Última actualización:** 2025-10-18
**Generado con:** Claude Code 🤖
