#!/usr/bin/env python3
"""Script para resetear la contraseña del usuario admin"""

from werkzeug.security import generate_password_hash
from app.db import Database

def reset_admin_password():
    # Nueva contraseña para admin
    new_password = "admin123"
    
    # Generar hash de la contraseña
    password_hash = generate_password_hash(new_password)
    
    # Actualizar en la base de datos
    query = "UPDATE users SET password_hash = ? WHERE username = 'admin'"
    result = Database.execute_query(query, (password_hash,), commit=True)
    
    print("=" * 50)
    print("✅ Contraseña del admin actualizada exitosamente")
    print("=" * 50)
    print(f"Usuario: admin")
    print(f"Contraseña: {new_password}")
    print("=" * 50)
    print("\n🌐 Accede en: http://localhost:5000/login")
    print()

if __name__ == '__main__':
    reset_admin_password()

