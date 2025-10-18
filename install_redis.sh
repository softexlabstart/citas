#!/bin/bash
# Script para instalar Redis en Amazon Linux 2/2023
# Ejecutar con: bash install_redis.sh

set -e  # Exit on error

echo "🚀 Instalando Redis..."

# Detectar el gestor de paquetes
if command -v zypper &> /dev/null; then
    PKG_MANAGER="zypper"
    REDIS_PKG="redis"
    REDIS_SERVICE="redis"
    echo "📦 Detectado: OpenSUSE (zypper)"
    UPDATE_CMD="zypper refresh"
    INSTALL_CMD="zypper install -y"
elif command -v dnf &> /dev/null; then
    PKG_MANAGER="dnf"
    REDIS_PKG="redis6"
    REDIS_SERVICE="redis6"
    echo "📦 Detectado: Amazon Linux 2023 (dnf)"
    UPDATE_CMD="dnf update -y"
    INSTALL_CMD="dnf install -y"
elif command -v yum &> /dev/null; then
    PKG_MANAGER="yum"
    REDIS_PKG="redis"
    REDIS_SERVICE="redis"
    echo "📦 Detectado: Amazon Linux 2 (yum)"
    UPDATE_CMD="yum update -y"
    INSTALL_CMD="yum install -y"
else
    echo "❌ ERROR: No se encontró zypper, dnf ni yum"
    exit 1
fi

# 1. Actualizar paquetes
echo "📦 Actualizando lista de paquetes..."
sudo $UPDATE_CMD

# 2. Instalar Redis
echo "⬇️  Instalando Redis ($REDIS_PKG)..."
sudo $INSTALL_CMD $REDIS_PKG

# 3. Iniciar Redis
echo "▶️  Iniciando Redis..."
sudo systemctl start $REDIS_SERVICE
sudo systemctl enable $REDIS_SERVICE

# 4. Verificar instalación
echo ""
echo "✅ Verificando instalación..."
if [ "$REDIS_SERVICE" == "redis6" ]; then
    redis6-cli --version
    redis6-cli ping
    REDIS_CONF="/etc/redis6/redis6.conf"
else
    redis-cli --version
    redis-cli ping
    REDIS_CONF="/etc/redis.conf"
fi

# 5. Configurar Redis para Celery
echo ""
echo "⚙️  Configurando Redis..."
# Backup de configuración original
if [ -f "$REDIS_CONF" ]; then
    sudo cp $REDIS_CONF ${REDIS_CONF}.backup

    # Permitir conexiones desde localhost (ya está por defecto pero verificamos)
    sudo sed -i 's/^bind .*/bind 127.0.0.1/' $REDIS_CONF

    # Aumentar max memory si es necesario (256MB)
    if ! grep -q "^maxmemory" $REDIS_CONF; then
        echo "maxmemory 256mb" | sudo tee -a $REDIS_CONF
        echo "maxmemory-policy allkeys-lru" | sudo tee -a $REDIS_CONF
    fi

    # Reiniciar para aplicar cambios
    sudo systemctl restart $REDIS_SERVICE
fi

# 6. Estado final
echo ""
echo "✅ Redis instalado correctamente!"
echo ""
echo "📊 Estado del servicio:"
sudo systemctl status $REDIS_SERVICE --no-pager

echo ""
echo "🔧 Comandos útiles:"
if [ "$REDIS_SERVICE" == "redis6" ]; then
    echo "   sudo systemctl start redis6      # Iniciar"
    echo "   sudo systemctl stop redis6       # Detener"
    echo "   sudo systemctl restart redis6    # Reiniciar"
    echo "   sudo systemctl status redis6     # Ver estado"
    echo "   redis6-cli ping                  # Probar conexión"
    echo "   redis6-cli monitor               # Ver comandos en tiempo real"
else
    echo "   sudo systemctl start redis       # Iniciar"
    echo "   sudo systemctl stop redis        # Detener"
    echo "   sudo systemctl restart redis     # Reiniciar"
    echo "   sudo systemctl status redis      # Ver estado"
    echo "   redis-cli ping                   # Probar conexión"
    echo "   redis-cli monitor                # Ver comandos en tiempo real"
fi
echo ""
echo "✨ Ahora puedes ejecutar: bash setup_celery.sh"
