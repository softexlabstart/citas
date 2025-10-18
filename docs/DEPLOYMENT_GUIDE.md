# Guía de Despliegue - Optimizaciones de Concurrencia

## Cambios Implementados

### 1. Throttling (Limitación de Requests)
- Usuarios anónimos: 100 req/hora
- Usuarios autenticados: 1000 req/hora
- Staff: 5000 req/hora

### 2. Caching
- Servicios y Recursos: Cache de 5 minutos
- Utiliza Redis para almacenamiento en caché

### 3. Optimización de Queries
- `select_related` para reducir queries N+1
- Índices de base de datos para mejorar performance

### 4. Configuración de Gunicorn
- Workers dinámicos basados en CPUs
- Worker class: `gevent` para mejor I/O
- Max 1000 requests por worker (previene memory leaks)

## Pasos de Despliegue en el Servidor

### 1. Instalar Dependencias

```bash
cd ~/appcitas
source venv/bin/activate
pip install gevent
```

### 2. Aplicar Migraciones de Base de Datos

```bash
cd citas/backend
python manage.py migrate
```

Esto creará los índices de base de datos para mejorar el performance.

### 3. Actualizar Gunicorn Service

Edita el archivo de servicio:
```bash
sudo nano /etc/systemd/system/gunicorn.service
```

Actualiza la línea `ExecStart` para usar el archivo de configuración:
```ini
[Unit]
Description=gunicorn daemon for proyecto-citas
After=network.target

[Service]
User=ec2-user
Group=ec2-user
WorkingDirectory=/home/ec2-user/appcitas/citas/backend
ExecStart=/home/ec2-user/appcitas/venv/bin/gunicorn \
    --config /home/ec2-user/appcitas/citas/backend/gunicorn_config.py \
    core.wsgi:application

[Install]
WantedBy=multi-user.target
```

### 4. Recargar y Reiniciar Servicios

```bash
sudo systemctl daemon-reload
sudo systemctl restart gunicorn
sudo systemctl status gunicorn
```

### 5. Verificar Logs

```bash
sudo journalctl -u gunicorn -f
```

Deberías ver algo como:
```
Server is ready. Spawning workers
[INFO] Listening at: unix:/home/ec2-user/appcitas/gunicorn.sock
[INFO] Using worker: gevent
[INFO] Booting worker with pid: XXXXX
```

## Monitoreo de Performance

### Ver Número de Workers Activos
```bash
ps aux | grep gunicorn | grep -v grep | wc -l
```

Deberías ver `workers + 1` procesos (1 master + N workers).

### Monitorear Uso de Memoria
```bash
ps aux | grep gunicorn | awk '{sum+=$6} END {print sum/1024 " MB"}'
```

### Ver Requests por Segundo (en logs)
```bash
sudo journalctl -u gunicorn --since "5 minutes ago" | grep "GET\|POST" | wc -l
```

## Limpieza de Cache (si es necesario)

Si necesitas limpiar el cache de Redis:
```bash
redis-cli
> SELECT 1
> FLUSHDB
> exit
```

## Rollback (si algo sale mal)

### Volver a configuración anterior de Gunicorn:
```bash
sudo nano /etc/systemd/system/gunicorn.service
```

Restaura la línea `ExecStart` original:
```ini
ExecStart=/home/ec2-user/appcitas/venv/bin/gunicorn --access-logfile - --workers 3 --bind unix:/home/ec2-user/appcitas/gunicorn.sock core.wsgi:application
```

```bash
sudo systemctl daemon-reload
sudo systemctl restart gunicorn
```

## Notas Adicionales

- **Logs de Debug**: Los prints están activos actualmente. En producción, considera removerlos para mejor performance.
- **Redis**: Asegúrate de que Redis esté corriendo: `sudo systemctl status redis`
- **PostgreSQL**: Verifica conexiones disponibles: `psql -c "SHOW max_connections;"`

## Métricas Esperadas

Con estas optimizaciones, deberías ver:
- **Reducción de latencia**: 30-50% más rápido en endpoints de listado
- **Mayor throughput**: 3-5x más requests por segundo
- **Menor uso de DB**: 40-60% menos queries por request
- **Cache hits**: 70-90% en datos de servicios/recursos
