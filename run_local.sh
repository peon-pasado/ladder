#!/bin/bash
# Script para ejecutar la aplicación en modo local con SQLite

# Limpiar variables de entorno que pueden causar problemas
unset DATABASE_URL
unset RENDER
unset PYTHONUNBUFFERED

# Activar el entorno virtual
source venv/bin/activate

# Configurar para desarrollo local
export FLASK_ENV=development
export FLASK_DEBUG=1

echo "=================================================="
echo "🚀 Iniciando Ladder App en modo DESARROLLO LOCAL"
echo "=================================================="
echo "Base de datos: SQLite (app.db)"
echo "Puerto: 5000"
echo "URL: http://localhost:5000"
echo "=================================================="
echo ""

# Ejecutar la aplicación
python app.py

