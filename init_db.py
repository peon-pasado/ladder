import sqlite3
import os
import sys
import psycopg2
from app.config import DATABASE_PATH, DB_TYPE, DATABASE_URL
from app.db import Database

def init_db():
    is_production = os.environ.get('FLASK_ENV') == 'production'
    using_postgres = os.environ.get('DATABASE_URL') is not None
    
    print(f"Inicializando base de datos {'PostgreSQL' if using_postgres and is_production else 'SQLite'} en {'producción' if is_production else 'desarrollo'}...")
    
    try:
        # Verificar si las tablas necesarias existen
        users_exists = Database.table_exists('users')
        
        if not users_exists:
            print("Creando tabla de usuarios...")
            # Crear tabla de usuarios
            if using_postgres and is_production:
                users_query = '''
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    email VARCHAR(100) UNIQUE NOT NULL,
                    password_hash VARCHAR(200) NOT NULL,
                    rating INTEGER DEFAULT 1500
                )
                '''
            else:
                users_query = '''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    rating INTEGER DEFAULT 1500
                )
                '''
            
            Database.execute_query(users_query, commit=True)
            print("Tabla de usuarios creada correctamente")
            
            # Crear tabla para cuentas de Baekjoon
            if using_postgres and is_production:
                baekjoon_query = '''
                CREATE TABLE IF NOT EXISTS baekjoon_accounts (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id),
                    baekjoon_username VARCHAR(50) NOT NULL,
                    added_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, baekjoon_username)
                )
                '''
            else:
                baekjoon_query = '''
                CREATE TABLE IF NOT EXISTS baekjoon_accounts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    baekjoon_username TEXT NOT NULL,
                    added_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    UNIQUE(user_id, baekjoon_username)
                )
                '''
            
            Database.execute_query(baekjoon_query, commit=True)
            print("Tabla de cuentas Baekjoon creada correctamente")
            
            # Crear tabla para problemas del ladder
            if using_postgres and is_production:
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
            else:
                ladder_query = '''
                CREATE TABLE IF NOT EXISTS ladder_problems (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    baekjoon_username TEXT NOT NULL,
                    position INTEGER NOT NULL,
                    problem_id TEXT NOT NULL,
                    problem_title TEXT NOT NULL,
                    state TEXT DEFAULT 'hidden',
                    UNIQUE(baekjoon_username, position)
                )
                '''
            
            Database.execute_query(ladder_query, commit=True)
            print("Tabla de problemas del ladder creada correctamente")
        
        # Verificar si la tabla de problemas resueltos existe
        solved_exists = Database.table_exists('solved_problems')
        
        if not solved_exists:
            print("Añadiendo tabla de problemas resueltos...")
            # Crear tabla para problemas resueltos con posición en leaderboard
            if using_postgres and is_production:
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
            else:
                solved_query = '''
                CREATE TABLE IF NOT EXISTS solved_problems (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    problem_id TEXT NOT NULL,
                    problem_title TEXT NOT NULL,
                    position INTEGER NOT NULL,
                    solved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    UNIQUE(user_id, problem_id)
                )
                '''
            
            Database.execute_query(solved_query, commit=True)
            print("Tabla de problemas resueltos añadida correctamente")
        
        # Verificar si la tabla de whitelist existe
        whitelist_exists = Database.table_exists('email_whitelist')
        
        if not whitelist_exists:
            print("Creando tabla para la whitelist de correos...")
            # Crear tabla para la whitelist de correos
            if using_postgres and is_production:
                whitelist_query = '''
                CREATE TABLE IF NOT EXISTS email_whitelist (
                    id SERIAL PRIMARY KEY,
                    email VARCHAR(100) UNIQUE NOT NULL,
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    notes TEXT
                )
                '''
            else:
                whitelist_query = '''
                CREATE TABLE IF NOT EXISTS email_whitelist (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT UNIQUE NOT NULL,
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    notes TEXT
                )
                '''
            
            Database.execute_query(whitelist_query, commit=True)
            print("Tabla de whitelist de correos creada correctamente")
        
        print(f"Base de datos inicializada correctamente.")
        
    except Exception as e:
        print(f"Error al inicializar la base de datos: {e}")
        sys.exit(1)

if __name__ == '__main__':
    init_db() 