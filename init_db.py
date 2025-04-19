import os
import sys
import psycopg2
from app.db import Database

def init_db():
    print(f"Inicializando base de datos PostgreSQL...")
    
    try:
        # Verificar si las tablas necesarias existen
        users_exists = Database.table_exists('users')
        
        if not users_exists:
            print("Creando tabla de usuarios...")
            users_query = '''
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                password_hash VARCHAR(200) NOT NULL,
                rating INTEGER DEFAULT 1500
            )
            '''
            
            Database.execute_query(users_query, commit=True)
            print("Tabla de usuarios creada correctamente")
            
            # Crear tabla para cuentas de Baekjoon
            baekjoon_query = '''
            CREATE TABLE IF NOT EXISTS baekjoon_accounts (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id),
                baekjoon_username VARCHAR(50) NOT NULL,
                added_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, baekjoon_username)
            )
            '''
            
            Database.execute_query(baekjoon_query, commit=True)
            print("Tabla de cuentas Baekjoon creada correctamente")
            
            # Crear tabla para problemas del ladder
            ladder_query = '''
            CREATE TABLE IF NOT EXISTS ladder_problems (
                id SERIAL PRIMARY KEY,
                baekjoon_username VARCHAR(50) NOT NULL,
                position INTEGER NOT NULL,
                problem_id VARCHAR(20) NOT NULL,
                problem_title VARCHAR(200) NOT NULL,
                state VARCHAR(20) DEFAULT 'hidden',
                UNIQUE(baekjoon_username, position)
            )
            '''
            
            Database.execute_query(ladder_query, commit=True)
            print("Tabla de problemas del ladder creada correctamente")
        
        # Verificar si la tabla de problemas resueltos existe
        solved_exists = Database.table_exists('solved_problems')
        
        if not solved_exists:
            print("Añadiendo tabla de problemas resueltos...")
            solved_query = '''
            CREATE TABLE IF NOT EXISTS solved_problems (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id),
                problem_id VARCHAR(20) NOT NULL,
                problem_title VARCHAR(200) NOT NULL,
                position INTEGER NOT NULL,
                solved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, problem_id)
            )
            '''
            
            Database.execute_query(solved_query, commit=True)
            print("Tabla de problemas resueltos añadida correctamente")
        
        # Verificar si la tabla de whitelist existe
        whitelist_exists = Database.table_exists('email_whitelist')
        
        if not whitelist_exists:
            print("Creando tabla para la whitelist de correos...")
            whitelist_query = '''
            CREATE TABLE IF NOT EXISTS email_whitelist (
                id SERIAL PRIMARY KEY,
                email VARCHAR(100) UNIQUE NOT NULL,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                notes TEXT
            )
            '''
            
            Database.execute_query(whitelist_query, commit=True)
            print("Tabla de whitelist de correos creada correctamente")
        
        print("Base de datos PostgreSQL inicializada correctamente.")
        
    except Exception as e:
        print(f"Error al inicializar la base de datos: {e}")
        sys.exit(1)

if __name__ == '__main__':
    init_db() 