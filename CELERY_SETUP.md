# 🚀 Configuración de Celery + Redis para Emails Asíncronos

Esta guía te ayudará a configurar Redis y Celery como servicios systemd en tu servidor de producción.

## 📋 Pre-requisitos

- ✅ Servidor Linux (soporta OpenSUSE, Amazon Linux 2/2023, Ubuntu, etc.)
- ✅ Python virtualenv configurado en `/home/ec2-user/appcitas/venv`
- ✅ Usuario `ec2-user` con permisos sudo
- ✅ Acceso al repositorio del proyecto

## 🛠️ Instalación Completa (Redis + Celery)

### Paso 1: Instalar Redis

Redis es necesario como message broker para Celery. El script detecta automáticamente tu distribución:

```bash
# En tu servidor de producción
cd ~/appcitas/citas
git pull origin main

# PRIMERO: Instalar Redis
bash install_redis.sh
```

**Distribuciones soportadas:**
- ✅ OpenSUSE (zypper) - Usa `redis-server.service`
- ✅ Amazon Linux 2023 (dnf) - Usa `redis6`
- ✅ Amazon Linux 2 (yum) - Usa `redis`

**Verificar instalación:**
```bash
# Ver estado del servicio
sudo systemctl status redis-server  # OpenSUSE
# O
sudo systemctl status redis6         # Amazon Linux 2023
# O
sudo systemctl status redis          # Amazon Linux 2

# Probar conexión
redis-cli ping  # Debe responder: PONG
```

### Paso 2: Configurar Celery

Una vez que Redis esté funcionando:

```bash
# Ejecutar script de instalación de Celery
bash setup_celery.sh
```

Este script:
1. ✅ Crea directorios para logs y PID files
2. ✅ Detecta automáticamente el servicio Redis correcto
3. ✅ Instala el servicio Celery en systemd
4. ✅ Inicia y habilita el worker de Celery
5. ✅ Verifica que todo esté funcionando

### Opción 2: Instalación Manual

```bash
# 1. Crear directorios
sudo mkdir -p /var/log/celery /var/run/celery
sudo chown -R ec2-user:ec2-user /var/log/celery /var/run/celery

# 2. Verificar Redis
sudo systemctl status redis
# Si no está corriendo:
sudo systemctl start redis
sudo systemctl enable redis

# 3. Instalar servicio
sudo cp celery.service /etc/systemd/system/
sudo chmod 644 /etc/systemd/system/celery.service
sudo systemctl daemon-reload

# 4. Iniciar Celery
sudo systemctl enable celery
sudo systemctl start celery

# 5. Verificar estado
sudo systemctl status celery
```

## ✅ Verificación

### 1. Verificar que Celery está corriendo

```bash
sudo systemctl status celery
```

Deberías ver: `Active: active (running)`

### 2. Ver logs en tiempo real

```bash
# Logs de systemd
sudo journalctl -u celery -f

# Logs del worker
tail -f /var/log/celery/worker.log
```

### 3. Probar envío de email

Desde tu aplicación, intenta enviar una invitación. Deberías ver en los logs:

```
[2025-10-18 11:30:00,000: INFO] Task usuarios.tasks.send_invitation_email_task[xxx] received
[2025-10-18 11:30:01,000: INFO] [Celery] Iniciando envío de invitación a user@example.com
[2025-10-18 11:30:02,000: INFO] [Celery] Invitación enviada exitosamente a user@example.com
[2025-10-18 11:30:02,000: INFO] Task usuarios.tasks.send_invitation_email_task[xxx] succeeded
```

## 🔧 Comandos Útiles

```bash
# Gestión del servicio
sudo systemctl start celery      # Iniciar
sudo systemctl stop celery       # Detener
sudo systemctl restart celery    # Reiniciar
sudo systemctl status celery     # Ver estado
sudo systemctl enable celery     # Auto-iniciar en boot
sudo systemctl disable celery    # Desactivar auto-inicio

# Logs
sudo journalctl -u celery -f              # Logs en tiempo real
sudo journalctl -u celery --since today   # Logs de hoy
tail -f /var/log/celery/worker.log        # Logs del worker

# Debugging
# Ejecutar Celery manualmente (útil para debug)
cd ~/appcitas/citas/backend
source ~/appcitas/venv/bin/activate
celery -A core worker --loglevel=debug
```

## 🐛 Troubleshooting

### Error: "celery.service could not be found"

**Solución:**
```bash
sudo systemctl daemon-reload
sudo systemctl start celery
```

### Error: "Connection refused" o "Redis connection error"

**Causa:** Redis no está corriendo

**Solución (depende de tu distro):**
```bash
# OpenSUSE
sudo systemctl status redis-server
sudo systemctl start redis-server
sudo systemctl enable redis-server

# Amazon Linux 2023
sudo systemctl status redis6
sudo systemctl start redis6
sudo systemctl enable redis6

# Amazon Linux 2 / Ubuntu
sudo systemctl status redis
sudo systemctl start redis
sudo systemctl enable redis
```

### Error: "Address already in use" al instalar Redis

**Causa:** Ya hay un proceso Redis corriendo en el puerto 6379

**Solución:**
```bash
# Ver qué está usando el puerto
sudo lsof -i :6379

# Si hay un proceso corriendo, verifica si es un servicio systemd
sudo systemctl list-units | grep redis

# Usa el servicio existente en lugar de crear uno nuevo
# Ejemplo: si ves redis-server.service, úsalo:
sudo systemctl start redis-server
sudo systemctl enable redis-server
redis-cli ping  # Debe responder PONG
```

### Error: "Failed listening on port 6379" con redis@redis

**Causa:** En OpenSUSE con servicio personalizado `redis-server.service`

**Solución:**
```bash
# Detener cualquier intento de usar redis@redis
sudo systemctl stop redis@redis 2>/dev/null
sudo systemctl disable redis@redis 2>/dev/null

# Usar el servicio correcto
sudo systemctl start redis-server
sudo systemctl enable redis-server
redis-cli ping
```

### Error: Tareas no se procesan

**Verificar:**
1. Que Redis esté corriendo: `sudo systemctl status redis`
2. Que Celery esté corriendo: `sudo systemctl status celery`
3. Revisar logs: `sudo journalctl -u celery -f`

### Error: "Permission denied" en logs

**Solución:**
```bash
sudo chown -R ec2-user:ec2-user /var/log/celery
sudo chown -R ec2-user:ec2-user /var/run/celery
sudo systemctl restart celery
```

## 📊 Monitoreo

### Ver tareas en cola

```bash
cd ~/appcitas/citas/backend
source ~/appcitas/venv/bin/activate
python manage.py shell

>>> from core.celery import app
>>> app.control.inspect().active()
>>> app.control.inspect().scheduled()
```

### Ver estadísticas del worker

```bash
celery -A core inspect stats
```

## 🔄 Actualizar después de cambios en código

Cada vez que modifiques tareas de Celery:

```bash
cd ~/appcitas/citas
git pull origin main
sudo systemctl restart celery
```

## 📝 Notas

- **Logs:** Los logs se rotan automáticamente por logrotate
- **Performance:** El worker usa `Nice=10` para no impactar el rendimiento del servidor
- **Auto-restart:** El servicio se reinicia automáticamente si falla
- **Base de datos Redis:** Usa DB 2 para Celery (DB 1 es para cache de Django)

## 🎯 Configuración Avanzada

### Múltiples Workers

Si necesitas más workers para manejar carga alta:

```bash
# Editar servicio
sudo nano /etc/systemd/system/celery.service

# Cambiar:
ExecStart=/home/ec2-user/appcitas/venv/bin/celery -A core worker \
    --concurrency=4 \
    --loglevel=info \
    ...

# Reiniciar
sudo systemctl daemon-reload
sudo systemctl restart celery
```

### Celery Beat (Tareas Programadas)

Si en el futuro necesitas tareas periódicas, puedes agregar Celery Beat.

## ✨ Beneficios

- ✅ **Envío asíncrono de emails** - La API responde instantáneamente (~100ms vs 2-3s)
- ✅ **Reintentos automáticos** - Si falla el envío, reintenta 3 veces con 60s de delay
- ✅ **Escalable** - Fácil agregar más workers con `--concurrency`
- ✅ **Monitoreable** - Logs centralizados en journald y archivos dedicados
- ✅ **Resiliente** - Auto-restart en caso de fallos
- ✅ **Multi-distribución** - Soporta OpenSUSE, Amazon Linux 2/2023, Ubuntu

---

## 📚 Archivos del Proyecto

### Scripts de Instalación

- **`install_redis.sh`**: Instalación automática de Redis
  - Detecta distribución (zypper/dnf/yum)
  - Instala y configura Redis
  - Crea configuración mínima si es necesario

- **`setup_celery.sh`**: Configuración automática de Celery
  - Detecta servicio Redis correcto (redis-server/redis@redis/redis6/redis)
  - Crea directorios necesarios
  - Instala y habilita servicio systemd

### Archivos de Configuración

- **`celery.service`**: Definición del servicio systemd
  - Usuario: `ec2-user`
  - Tipo: `forking`
  - PID file: `/var/run/celery/worker.pid`
  - Logs: `/var/log/celery/worker.log`

- **`backend/usuarios/tasks.py`**: Tareas de Celery
  - `send_invitation_email_task`: Envío asíncrono de invitaciones
  - Reintentos: 3 intentos, 60s de delay
  - Logging completo

- **`backend/core/celery.py`**: Configuración de Celery app
  - Broker: Redis DB 2 (`redis://127.0.0.1:6379/2`)
  - Result backend: Redis DB 2
  - Autodiscovery de tareas

---

## 🎯 Resumen de Cambios Implementados

### Backend

1. **`backend/usuarios/tasks.py`** (NUEVO)
   - Tarea `send_invitation_email_task` con reintentos automáticos

2. **`backend/usuarios/views.py`**
   - `InvitationView` usa `.delay()` para envío asíncrono
   - `ClientViewSet.history()` incluye datos del cliente (optimización)

3. **`backend/core/settings.py`**
   - Configuración de Celery (broker, result backend, serializers)

4. **`backend/core/celery.py`**
   - Inicialización de app Celery
   - Autodiscovery de tareas

### Frontend

1. **`frontend/src/components/ClientHistoryModal.tsx`**
   - Usa datos del cliente desde `history.client`
   - Elimina llamada duplicada a API

### Infraestructura

1. **`install_redis.sh`**
   - Instalación multi-distribución de Redis

2. **`setup_celery.sh`**
   - Configuración automática de Celery worker

3. **`celery.service`**
   - Servicio systemd para Celery

---

**Última actualización:** 2025-10-18
**Documentación generada por Claude Code** 🤖
