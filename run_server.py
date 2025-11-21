#!/usr/bin/env python3
"""Script para ejecutar el servidor en un puerto alternativo si 5000 está ocupado"""
import os
import socket

# Limpiar variables de entorno
if 'DATABASE_URL' in os.environ:
    del os.environ['DATABASE_URL']
if 'RENDER' in os.environ:
    del os.environ['RENDER']

from app import create_app

app = create_app()

def get_local_ip():
    """Obtener la IP local de la máquina"""
    try:
        # Crear un socket para obtener la IP local
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception:
        return "No disponible"

if __name__ == '__main__':
    # Intentar puerto 5000, si no funciona usar 5001
    port = 5000
    local_ip = get_local_ip()
    
    try:
        print("\n" + "=" * 70)
        print("  LADDER APP - SERVIDOR INICIADO")
        print("=" * 70)
        print(f"Base de datos: SQLite (app.db)")
        print(f"Modo: Desarrollo")
        print(f"Puerto: {port}")
        print("=" * 70)
        print("\nACCESO LOCAL (desde esta computadora):")
        print(f"  http://localhost:{port}")
        print(f"  http://127.0.0.1:{port}")
        print("\nACCESO DESDE OTROS DISPOSITIVOS EN LA RED:")
        print(f"  http://{local_ip}:{port}")
        print("\n" + "=" * 70)
        print("Presiona Ctrl+C para detener el servidor")
        print("=" * 70 + "\n")
        
        app.run(host='0.0.0.0', port=port, debug=True)
    except OSError as e:
        if "Address already in use" in str(e):
            port = 5001
            print(f"\nPuerto 5000 ocupado, usando puerto {port}")
            print(f"Acceso local: http://localhost:{port}")
            print(f"Acceso en red: http://{local_ip}:{port}\n")
            app.run(host='0.0.0.0', port=port, debug=True)
        else:
            raise

