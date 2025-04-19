#!/usr/bin/env python
import os
import sys
from werkzeug.security import generate_password_hash
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def create_admin():
    # Credenciales del administrador
    admin_username = "admin"
    admin_email = "admin@ejemplo.com"
    admin_password = "admin123"  # Cambiar por una contraseña segura
    
    # Obtener la URL de conexión
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("ERROR: No se encontró DATABASE_URL")
        sys.exit(1)
    
    print(f"Conectando a PostgreSQL para crear admin...")
    
    try:
        # Establecer conexión
        conn = psycopg2.connect(database_url)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Crear tabla de usuarios si no existe
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            password_hash VARCHAR(200) NOT NULL,
            rating INTEGER DEFAULT 1500
        )
        ''')
        print("Tabla users creada o verificada")
        
        # Verificar si el admin ya existe
        cursor.execute("SELECT id FROM users WHERE username = %s OR email = %s", 
                      (admin_username, admin_email))
        admin_exists = cursor.fetchone()
        
        if admin_exists:
            print(f"El usuario administrador ya existe (ID: {admin_exists[0]})")
        else:
            # Crear el usuario administrador
            password_hash = generate_password_hash(admin_password)
            cursor.execute('''
            INSERT INTO users (username, email, password_hash, rating) 
            VALUES (%s, %s, %s, %s)
            ''', (admin_username, admin_email, password_hash, 2000))
            
            # Obtener el ID del admin
            cursor.execute("SELECT id FROM users WHERE username = %s", (admin_username,))
            admin_id = cursor.fetchone()[0]
            print(f"Usuario administrador creado (ID: {admin_id})")
            
            # Crear las tablas relacionadas
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS baekjoon_accounts (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id),
                baekjoon_username VARCHAR(50) NOT NULL,
                added_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, baekjoon_username)
            )
            ''')
            print("Tabla baekjoon_accounts creada o verificada")
            
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS ladder_problems (
                id SERIAL PRIMARY KEY,
                baekjoon_username VARCHAR(50) NOT NULL,
                position INTEGER NOT NULL,
                problem_id VARCHAR(20) NOT NULL,
                problem_title VARCHAR(200) NOT NULL,
                state VARCHAR(20) DEFAULT 'hidden',
                UNIQUE(baekjoon_username, position)
            )
            ''')
            print("Tabla ladder_problems creada o verificada")
            
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS solved_problems (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id),
                problem_id VARCHAR(20) NOT NULL,
                problem_title VARCHAR(200) NOT NULL,
                position INTEGER NOT NULL,
                solved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, problem_id)
            )
            ''')
            print("Tabla solved_problems creada o verificada")
            
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS email_whitelist (
                id SERIAL PRIMARY KEY,
                email VARCHAR(100) UNIQUE NOT NULL,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                notes TEXT
            )
            ''')
            print("Tabla email_whitelist creada o verificada")
            
            # Agregar correo del administrador a la whitelist
            cursor.execute('''
            INSERT INTO email_whitelist (email, notes) 
            VALUES (%s, %s)
            ''', (admin_email, "Administrador del sistema"))
            print(f"Correo {admin_email} añadido a la whitelist")
        
        # Cerrar conexión
        cursor.close()
        conn.close()
        
        print("\nProceso completado con éxito")
        print(f"Usuario: {admin_username}")
        print(f"Contraseña: {admin_password}")
        print("Recuerda cambiar la contraseña después del primer inicio de sesión")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    create_admin() 