#!/bin/bash
# Script para instalar Redis en Amazon Linux 2023
# Ejecutar con: bash install_redis.sh

set -e  # Exit on error

echo "🚀 Instalando Redis en Amazon Linux 2023..."

# 1. Actualizar paquetes
echo "📦 Actualizando lista de paquetes..."
sudo dnf update -y

# 2. Instalar Redis
echo "⬇️  Instalando Redis..."
sudo dnf install -y redis6

# 3. Iniciar Redis
echo "▶️  Iniciando Redis..."
sudo systemctl start redis6
sudo systemctl enable redis6

# 4. Verificar instalación
echo ""
echo "✅ Verificando instalación..."
redis6-cli --version
redis6-cli ping

# 5. Configurar Redis para Celery
echo ""
echo "⚙️  Configurando Redis..."
# Backup de configuración original
sudo cp /etc/redis6/redis6.conf /etc/redis6/redis6.conf.backup

# Permitir conexiones desde localhost (ya está por defecto pero verificamos)
sudo sed -i 's/^bind .*/bind 127.0.0.1/' /etc/redis6/redis6.conf

# Aumentar max memory si es necesario (256MB)
if ! grep -q "^maxmemory" /etc/redis6/redis6.conf; then
    echo "maxmemory 256mb" | sudo tee -a /etc/redis6/redis6.conf
    echo "maxmemory-policy allkeys-lru" | sudo tee -a /etc/redis6/redis6.conf
fi

# Reiniciar para aplicar cambios
sudo systemctl restart redis6

# 6. Estado final
echo ""
echo "✅ Redis instalado correctamente!"
echo ""
echo "📊 Estado del servicio:"
sudo systemctl status redis6 --no-pager

echo ""
echo "🔧 Comandos útiles:"
echo "   sudo systemctl start redis6      # Iniciar"
echo "   sudo systemctl stop redis6       # Detener"
echo "   sudo systemctl restart redis6    # Reiniciar"
echo "   sudo systemctl status redis6     # Ver estado"
echo "   redis6-cli ping                  # Probar conexión"
echo "   redis6-cli monitor               # Ver comandos en tiempo real"
echo ""
echo "✨ Ahora puedes ejecutar: bash setup_celery.sh"
