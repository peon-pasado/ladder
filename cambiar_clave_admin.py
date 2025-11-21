#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Script para cambiar la contrasena del administrador"""
import sqlite3
from werkzeug.security import generate_password_hash
import sys

def cambiar_password(nueva_password):
    """Cambia la contrasena del admin"""
    
    # Generar hash de la contrasena
    password_hash = generate_password_hash(nueva_password)
    
    # Conectar a la base de datos
    conn = sqlite3.connect('app.db')
    cursor = conn.cursor()
    
    # Actualizar la contrasena del admin
    cursor.execute(
        "UPDATE users SET password_hash = ? WHERE username = 'admin'",
        (password_hash,)
    )
    
    # Verificar si se actualizo
    if cursor.rowcount > 0:
        conn.commit()
        print("")
        print("========================================")
        print("  CONTRASENA ACTUALIZADA EXITOSAMENTE")
        print("========================================")
        print("")
        print("Usuario: admin")
        print("Nueva contrasena: " + nueva_password)
        print("")
        print("========================================")
    else:
        print("")
        print("ERROR: No se encontro el usuario 'admin' en la base de datos")
        print("")
        print("Ejecuta primero: python init_db.py")
        print("")
    
    conn.close()

if __name__ == "__main__":
    print("")
    print("========================================")
    print("  CAMBIAR CONTRASENA DEL ADMIN")
    print("========================================")
    print("")
    
    # Verificar si se paso la contrasena como argumento
    if len(sys.argv) > 1:
        nueva_password = sys.argv[1]
    else:
        # Solicitar la nueva contrasena
        nueva_password = input("Ingresa la nueva contrasena para admin: ")
    
    if not nueva_password or len(nueva_password) < 6:
        print("ERROR: La contrasena debe tener al menos 6 caracteres")
        sys.exit(1)
    
    cambiar_password(nueva_password)

