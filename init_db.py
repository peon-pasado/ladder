import os
import sys
import psycopg2
import sqlite3
from app.config import DB_TYPE, DATABASE_URL, DATABASE_PATH

def init_db():
    print(f"=== INICIO DE INIT_DB ===")
    print(f"Tipo de base de datos: {DB_TYPE}")
    print(f"URL de conexión: {DATABASE_URL}")
    
    try:
        # Validar si podemos conectarnos
        if DB_TYPE == 'postgresql':
            print("Intentando conectar a PostgreSQL...")
            conn = psycopg2.connect(DATABASE_URL)
            print("Conexión a PostgreSQL establecida")
            conn.close()
        else:
            print("Intentando conectar a SQLite...")
            conn = sqlite3.connect(DATABASE_PATH)
            print("Conexión a SQLite establecida")
            conn.close()
        
        print("Importando Database...")
        from app.db import Database
        
        # Verificar si las tablas necesarias existen
        print("Verificando si existe tabla users...")
        users_exists = Database.table_exists('users')
        print(f"¿Existe tabla users? {users_exists}")
        
        if not users_exists:
            print("Creando tabla de usuarios...")
            # Crear tabla de usuarios
            if DB_TYPE == 'postgresql':
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
            
            print(f"Ejecutando query: {users_query}")
            result = Database.execute_query(users_query, commit=True)
            print(f"Resultado: {result}")
            print("Tabla de usuarios creada correctamente")
            
            # Crear tabla para cuentas de Baekjoon
            print("Creando tabla de cuentas Baekjoon...")
            if DB_TYPE == 'postgresql':
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
            
            print(f"Ejecutando query: {baekjoon_query}")
            result = Database.execute_query(baekjoon_query, commit=True)
            print(f"Resultado: {result}")
            print("Tabla de cuentas Baekjoon creada correctamente")
            
            # Crear tabla para problemas del ladder
            if DB_TYPE == 'postgresql':
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
            if DB_TYPE == 'postgresql':
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
            if DB_TYPE == 'postgresql':
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
        
        print(f"Base de datos {DB_TYPE} inicializada correctamente.")
        print("=== FIN DE INIT_DB ===")
        
    except Exception as e:
        print(f"ERROR en init_db: {e}")
        print(f"Tipo de error: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    init_db() 