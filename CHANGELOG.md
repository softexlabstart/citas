# Changelog

Todos los cambios notables del proyecto serán documentados en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/),
y este proyecto adhiere a [Versionado Semántico](https://semver.org/lang/es/).

## [2.0.0] - 2025-10-18

### Added
- **Emails asíncronos con Celery**: Envío de invitaciones sin bloquear requests HTTP
- **Optimización de historial de cliente**: Reducción de llamadas API de 2 a 1
- **Página de reportes unificada**: 3 tabs (Dashboard Financiero, Reporte de Citas, Reporte por Sede)
- **Configuración completa de Celery + Redis**: Scripts de instalación automatizados
- **Documentación consolidada**: Estructura organizada en carpeta `docs/`
- **Scripts de deployment**: Carpeta `scripts/` con instaladores de Redis y Celery
- **`.env.example`**: Template de variables de entorno para nuevos desarrolladores
- **`.gitignore` mejorado**: Protección contra commits accidentales
- **Badges en README**: Tecnologías y versiones visibles
- **Tabla de contenidos en README**: Navegación mejorada
- **CHANGELOG.md**: Este archivo para trackear versiones

### Changed
- **Estructura de documentación**: Movida a `docs/` con índice organizado
- **README.md**: Completamente renovado con quick start y enlaces claros
- **Celery service**: Configuración mejorada con manejo correcto de PID files
- **Frontend**: ClientHistoryModal optimizado para usar datos del backend
- **Backend**: DashboardSummaryView optimizado para prevenir timeouts

### Fixed
- **Celery ExecStop**: Solucionado error de variable $MAINPID no definida
- **Redis service detection**: Soporte multi-distribución (OpenSUSE, Amazon Linux)
- **Worker timeouts**: Optimización de queries en dashboard con límite de 500 citas
- **FieldError en dashboard**: Removido `.only()` que causaba conflicto con `select_related`

### Removed
- Archivos de documentación redundantes (3 archivos sobre registro → 1)
- `INSTALL_RECHARTS.md` (info integrada en README)
- `package.json` duplicado en raíz
- `manage.py` duplicado en raíz
- `README_OLD.md`

### Performance
- **Rate Limiting**: 100 req/h anónimos, 1000 req/h autenticados, 5000 req/h staff
- **Redis Cache**: Caché de 5 minutos para servicios y recursos
- **Query Optimization**: `select_related` y `prefetch_related` en viewsets
- **Database Indexes**: Índices en modelos Cita, Servicio, Colaborador, Bloqueo
- **Gunicorn con Gevent**: Workers optimizados para I/O

### Security
- **Django-Axes**: Bloqueo después de 5 intentos fallidos de login
- **CORS configurado**: Origins específicos (no wildcard)
- **CSP Headers**: Content Security Policy implementado
- **Security headers**: Condicionales según DEBUG (HSTS, SSL redirect, etc.)

### Infrastructure
- **Celery como servicio systemd**: Configuración con auto-restart
- **Redis multi-distro**: Soporte para OpenSUSE, Amazon Linux 2/2023, Ubuntu
- **Scripts automatizados**: `install_redis.sh` y `setup_celery.sh`

## [1.0.0] - 2025-09-01

### Added
- Sistema base multi-tenant con Django + React
- Autenticación JWT con tokens de refresh
- Gestión de citas con estados (Pendiente, Confirmada, Asistió, etc.)
- Roles diferenciados (Cliente, Colaborador, Admin Sede, Superusuario)
- Registro por organización con URLs personalizadas
- Dashboard financiero con Recharts
- Visualización de calendario con React Big Calendar
- Reportes exportables a CSV
- Internacionalización con i18next
- Panel de administración de Django
- API RESTful completa
- Sistema de disponibilidad de horarios
- Bloqueos de colaboradores
- Notificaciones por email
- Reservas anónimas

### Infrastructure
- PostgreSQL como base de datos
- Gunicorn como WSGI server
- Configuración para deployment en producción

---

## Tipos de cambios

- `Added` - Nueva funcionalidad
- `Changed` - Cambios en funcionalidad existente
- `Deprecated` - Funcionalidad que será removida
- `Removed` - Funcionalidad removida
- `Fixed` - Corrección de bugs
- `Security` - Mejoras de seguridad
- `Performance` - Mejoras de rendimiento
- `Infrastructure` - Cambios en infraestructura o deployment

---

**Mantenido por:** Equipo de Desarrollo  
**Formato:** [Keep a Changelog](https://keepachangelog.com/)  
**Versionado:** [Semantic Versioning](https://semver.org/)
