#!/usr/bin/env python3
"""Script para ejecutar el servidor en un puerto alternativo si 5000 está ocupado"""
import os

# Limpiar variables de entorno
if 'DATABASE_URL' in os.environ:
    del os.environ['DATABASE_URL']
if 'RENDER' in os.environ:
    del os.environ['RENDER']

from app import create_app

app = create_app()

if __name__ == '__main__':
    # Intentar puerto 5000, si no funciona usar 5001
    port = 5000
    try:
        print(f"🚀 Iniciando Ladder App en http://localhost:{port}")
        print("=" * 60)
        print("✓ Base de datos: SQLite (app.db)")
        print("✓ Modo: Desarrollo")
        print("=" * 60)
        print(f"\n👉 Abre tu navegador en: http://localhost:{port}\n")
        app.run(host='127.0.0.1', port=port, debug=True)
    except OSError as e:
        if "Address already in use" in str(e):
            port = 5001
            print(f"⚠️  Puerto 5000 ocupado, usando puerto {port}")
            print(f"👉 Abre tu navegador en: http://localhost:{port}\n")
            app.run(host='127.0.0.1', port=port, debug=True)
        else:
            raise

