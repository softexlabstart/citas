# Scripts de Deployment

Esta carpeta contiene scripts y archivos de configuración para el deployment del sistema en producción.

## 📁 Contenido

### Scripts de Instalación

- **`install_redis.sh`** - Instalación automática de Redis con detección multi-distribución
  - Soporta: OpenSUSE (zypper), Amazon Linux 2023 (dnf), Amazon Linux 2 (yum)
  - Detecta y configura el servicio correcto según la distribución
  - Maneja redis-server, redis@redis, redis6, redis

- **`setup_celery.sh`** - Configuración automática de Celery worker como servicio systemd
  - Crea directorios necesarios (/var/log/celery, /var/run/celery)
  - Detecta servicio Redis activo
  - Instala y habilita celery.service
  - Verifica funcionamiento

### Archivos Systemd (`systemd/`)

- **`celery.service`** - Servicio systemd para Celery worker
  - Configurado con Type=forking
  - Auto-restart en caso de fallos
  - Logs en /var/log/celery/worker.log
  - PID file para gestión correcta de procesos

- **`gunicorn.service`** - Servicio systemd para Gunicorn (backend)
  - Worker principal de Django
  - Configurado con gunicorn_config.py

- **`gunicorn-frontend.service`** - Servicio alternativo para frontend estático
  - (Si se necesita servir el build de React con Gunicorn)

## 🚀 Uso Rápido

### Instalar Redis

```bash
# Desde la raíz del proyecto
bash scripts/install_redis.sh
```

### Configurar Celery

```bash
# Desde la raíz del proyecto
bash scripts/setup_celery.sh
```

### Instalar servicios manualmente

```bash
# Copiar archivos de servicio
sudo cp scripts/systemd/celery.service /etc/systemd/system/
sudo cp scripts/systemd/gunicorn.service /etc/systemd/system/

# Recargar systemd
sudo systemctl daemon-reload

# Habilitar e iniciar
sudo systemctl enable celery gunicorn
sudo systemctl start celery gunicorn

# Verificar estado
sudo systemctl status celery gunicorn
```

## 📖 Documentación Completa

Ver [CELERY_SETUP.md](../CELERY_SETUP.md) en la raíz del proyecto para:
- Guía paso a paso completa
- Troubleshooting
- Configuración avanzada
- Monitoreo de servicios

## 🔧 Requisitos

- Sistema operativo Linux (OpenSUSE, Amazon Linux, Ubuntu, etc.)
- Python virtualenv en `/home/ec2-user/appcitas/venv` (o ajustar rutas en los archivos)
- Usuario con permisos sudo
- Git para clonar/actualizar el repositorio

## ⚠️ Notas Importantes

1. **Rutas hardcodeadas**: Los scripts asumen rutas específicas (`/home/ec2-user/appcitas`). Ajusta según tu instalación.

2. **Usuario**: Los servicios systemd ejecutan como `ec2-user`. Cambia en los archivos `.service` si usas otro usuario.

3. **Redis DB**: Celery usa Redis DB 2 por defecto. Configurado en `backend/core/settings.py`.

4. **Logs**: Los logs de Celery se guardan en `/var/log/celery/worker.log`. Asegúrate de tener permisos.

## 🐛 Troubleshooting

### Redis no inicia

```bash
# Verificar qué servicio está disponible
sudo systemctl list-unit-files | grep redis

# Intentar con el nombre correcto
sudo systemctl start redis-server  # OpenSUSE
sudo systemctl start redis6         # Amazon Linux 2023
sudo systemctl start redis          # Amazon Linux 2
```

### Celery no inicia

```bash
# Ver logs detallados
sudo journalctl -u celery -n 50

# Verificar que Redis está corriendo
redis-cli ping

# Verificar permisos de directorios
ls -la /var/log/celery /var/run/celery
```

### PID file errors

```bash
# Limpiar PID files viejos
sudo rm /var/run/celery/worker.pid

# Reiniciar servicio
sudo systemctl restart celery
```

---

**Mantenido por:** Equipo de Desarrollo  
**Última actualización:** 2025-10-18
