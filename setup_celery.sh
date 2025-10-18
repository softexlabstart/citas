#!/bin/bash
# Script para configurar Celery como servicio systemd
# Ejecutar con: bash setup_celery.sh

set -e  # Exit on error

echo "🚀 Configurando Celery Worker para Proyecto Citas..."

# 1. Crear directorios necesarios
echo "📁 Creando directorios para logs y PID files..."
sudo mkdir -p /var/log/celery
sudo mkdir -p /var/run/celery
sudo chown -R ec2-user:ec2-user /var/log/celery
sudo chown -R ec2-user:ec2-user /var/run/celery

# 2. Verificar que Redis está corriendo
echo "🔍 Verificando Redis..."
# Intentar con diferentes nombres de servicio según la distro
if sudo systemctl is-active --quiet redis-server; then
    echo "✅ Redis-server está corriendo"
elif sudo systemctl is-active --quiet redis@redis; then
    echo "✅ Redis@redis está corriendo (OpenSUSE)"
elif sudo systemctl is-active --quiet redis6; then
    echo "✅ Redis6 está corriendo"
elif sudo systemctl is-active --quiet redis; then
    echo "✅ Redis está corriendo"
else
    echo "⚠️  Redis no está corriendo. Intentando iniciar..."
    if sudo systemctl start redis-server 2>/dev/null; then
        sudo systemctl enable redis-server
        echo "✅ Redis-server iniciado"
    elif sudo systemctl start redis@redis 2>/dev/null; then
        sudo systemctl enable redis@redis
        echo "✅ Redis@redis iniciado (OpenSUSE)"
    elif sudo systemctl start redis6 2>/dev/null; then
        sudo systemctl enable redis6
        echo "✅ Redis6 iniciado"
    elif sudo systemctl start redis 2>/dev/null; then
        sudo systemctl enable redis
        echo "✅ Redis iniciado"
    else
        echo "❌ ERROR: Redis no está instalado"
        echo ""
        echo "Por favor, instala Redis primero:"
        echo "  bash install_redis.sh"
        echo ""
        exit 1
    fi
fi

# 3. Copiar archivo de servicio
echo "📝 Instalando servicio Celery..."
sudo cp celery.service /etc/systemd/system/celery.service
sudo chmod 644 /etc/systemd/system/celery.service

# 4. Reload systemd
echo "🔄 Recargando systemd..."
sudo systemctl daemon-reload

# 5. Habilitar y arrancar servicio
echo "▶️  Iniciando Celery worker..."
sudo systemctl enable celery
sudo systemctl start celery

# 6. Verificar estado
echo ""
echo "✅ Configuración completada!"
echo ""
echo "📊 Estado del servicio:"
sudo systemctl status celery --no-pager

echo ""
echo "📝 Ver logs en tiempo real:"
echo "   sudo journalctl -u celery -f"
echo ""
echo "🔧 Comandos útiles:"
echo "   sudo systemctl start celery     # Iniciar"
echo "   sudo systemctl stop celery      # Detener"
echo "   sudo systemctl restart celery   # Reiniciar"
echo "   sudo systemctl status celery    # Ver estado"
echo "   tail -f /var/log/celery/worker.log  # Ver logs del worker"
