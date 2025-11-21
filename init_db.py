#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para inicializar la base de datos con las credenciales por defecto.
Solo ejecutar la primera vez o para resetear la base de datos.
"""
import sqlite3
from werkzeug.security import generate_password_hash

# Credenciales por defecto
DEFAULT_USERNAME = "admin"
DEFAULT_PASSWORD = "admin123"
DEFAULT_EMAIL = "admin@ladder.local"

def init_database():
    """Inicializa la base de datos con las tablas y usuario admin por defecto"""
    
    print("========================================")
    print("  INICIALIZANDO BASE DE DATOS")
    print("========================================")
    print("")
    
    # Conectar a la base de datos
    conn = sqlite3.connect('app.db')
    cursor = conn.cursor()
    
    # Crear tabla de usuarios
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username VARCHAR(50) UNIQUE NOT NULL,
        email VARCHAR(100) UNIQUE NOT NULL,
        password_hash VARCHAR(200) NOT NULL,
        rating INTEGER DEFAULT 1500,
        is_admin INTEGER DEFAULT 0
    )
    ''')
    
    # Crear tabla de cuentas de Baekjoon
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS baekjoon_accounts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        baekjoon_username VARCHAR(50) NOT NULL,
        added_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(user_id, baekjoon_username),
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    ''')
    
    # Crear tabla de problemas del ladder
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS ladder_problems (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        baekjoon_username VARCHAR(50) NOT NULL,
        position INTEGER NOT NULL,
        problem_id VARCHAR(20) NOT NULL,
        problem_title VARCHAR(200) NOT NULL,
        state VARCHAR(20) DEFAULT 'hidden',
        revealed_at TIMESTAMP,
        UNIQUE(baekjoon_username, position)
    )
    ''')
    
    # Crear tabla de problemas resueltos
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS solved_problems (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        problem_id VARCHAR(20) NOT NULL,
        problem_title VARCHAR(200) NOT NULL,
        position INTEGER NOT NULL,
        solved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(user_id, problem_id),
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    ''')
    
    # Crear tabla de problemas
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS problems (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        problem_id VARCHAR(20) UNIQUE NOT NULL,
        problem_title VARCHAR(200) NOT NULL,
        tier INTEGER,
        tags TEXT,
        level INTEGER,
        solved_count INTEGER DEFAULT 0,
        accepted_user_count INTEGER DEFAULT 0,
        average_tries REAL DEFAULT 0.0,
        source_group VARCHAR(100)
    )
    ''')
    
    # Crear tabla de whitelist de emails
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS email_whitelist (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email VARCHAR(100) UNIQUE NOT NULL,
        added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        notes TEXT
    )
    ''')
    
    print("Tablas creadas correctamente")
    print("")
    
    # Verificar si ya existe el usuario admin
    cursor.execute("SELECT id FROM users WHERE username = ?", (DEFAULT_USERNAME,))
    existing_admin = cursor.fetchone()
    
    if existing_admin:
        print("ADVERTENCIA: El usuario 'admin' ya existe")
        print("No se creara un nuevo usuario admin")
        print("")
        print("Si quieres resetear la contrasena, usa:")
        print("  python cambiar_clave_admin.py")
    else:
        # Crear usuario admin por defecto
        password_hash = generate_password_hash(DEFAULT_PASSWORD)
        
        cursor.execute('''
        INSERT INTO users (username, email, password_hash, rating, is_admin)
        VALUES (?, ?, ?, 1500, 1)
        ''', (DEFAULT_USERNAME, DEFAULT_EMAIL, password_hash))
        
        print("Usuario administrador creado:")
        print(f"  Usuario:    {DEFAULT_USERNAME}")
        print(f"  Contrasena: {DEFAULT_PASSWORD}")
        print(f"  Email:      {DEFAULT_EMAIL}")
        print("")
        print("IMPORTANTE: Cambia la contrasena despues de iniciar sesion")
    
    conn.commit()
    conn.close()
    
    print("")
    print("========================================")
    print("  BASE DE DATOS INICIALIZADA")
    print("========================================")
    print("")

if __name__ == "__main__":
    import os
    
    # Verificar si ya existe la base de datos
    if os.path.exists('app.db'):
        print("")
        print("ADVERTENCIA: Ya existe una base de datos (app.db)")
        respuesta = input("Deseas continuar? Esto puede crear tablas faltantes (s/n): ")
        if respuesta.lower() != 's':
            print("Operacion cancelada")
            exit(0)
    
    init_database()

