# 🚀 Configuración de Celery para Emails Asíncronos

Esta guía te ayudará a configurar Celery como servicio systemd en tu servidor de producción.

## 📋 Pre-requisitos

- ✅ Redis instalado y corriendo
- ✅ Python virtualenv configurado en `/home/ec2-user/appcitas/venv`
- ✅ Usuario `ec2-user` con permisos adecuados

## 🛠️ Instalación Rápida

### Opción 1: Script Automático (Recomendado)

```bash
# En tu servidor de producción
cd ~/appcitas/citas
git pull origin main

# Ejecutar script de instalación
bash setup_celery.sh
```

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

**Solución:**
```bash
sudo systemctl status redis
sudo systemctl start redis
sudo systemctl enable redis
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

- ✅ **Envío asíncrono de emails** - La API responde instantáneamente
- ✅ **Reintentos automáticos** - Si falla el envío, reintenta 3 veces
- ✅ **Escalable** - Fácil agregar más workers
- ✅ **Monitoreable** - Logs centralizados en journald
- ✅ **Resiliente** - Auto-restart en caso de fallos

---

**Documentación generada por Claude Code** 🤖
