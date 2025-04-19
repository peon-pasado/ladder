#!/usr/bin/env python
import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def setup_postgres():
    """
    Script independiente para inicializar la base de datos PostgreSQL.
    Se conecta directamente a PostgreSQL y crea las tablas necesarias.
    """
    # Obtener la URL de conexión
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("ERROR: No se encontró DATABASE_URL")
        sys.exit(1)
    
    print(f"Conectando a PostgreSQL con URL: {database_url}")
    
    try:
        # Establecer conexión
        conn = psycopg2.connect(database_url)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Verificar el esquema actual
        cursor.execute("SELECT current_schema()")
        current_schema = cursor.fetchone()[0]
        print(f"Esquema actual: {current_schema}")
        
        # Establecer esquema 'public'
        cursor.execute("SET search_path TO public")
        
        # Verificar usuario y permisos
        cursor.execute("SELECT current_user")
        current_user = cursor.fetchone()[0]
        print(f"Usuario actual: {current_user}")
        
        cursor.execute("SELECT current_database()")
        current_db = cursor.fetchone()[0]
        print(f"Base de datos actual: {current_db}")
        
        # Crear tablas
        print("Creando tablas en esquema 'public'...")
        
        # Tabla de usuarios
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS public.users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            password_hash VARCHAR(200) NOT NULL,
            rating INTEGER DEFAULT 1500
        )
        ''')
        print("Tabla users creada")
        
        # Tabla de cuentas Baekjoon
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS public.baekjoon_accounts (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES public.users(id),
            baekjoon_username VARCHAR(50) NOT NULL,
            added_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, baekjoon_username)
        )
        ''')
        print("Tabla baekjoon_accounts creada")
        
        # Tabla de problemas del ladder
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS public.ladder_problems (
            id SERIAL PRIMARY KEY,
            baekjoon_username VARCHAR(50) NOT NULL,
            position INTEGER NOT NULL,
            problem_id VARCHAR(20) NOT NULL,
            problem_title VARCHAR(200) NOT NULL,
            state VARCHAR(20) DEFAULT 'hidden',
            UNIQUE(baekjoon_username, position)
        )
        ''')
        print("Tabla ladder_problems creada")
        
        # Tabla de problemas resueltos
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS public.solved_problems (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES public.users(id),
            problem_id VARCHAR(20) NOT NULL,
            problem_title VARCHAR(200) NOT NULL,
            position INTEGER NOT NULL,
            solved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, problem_id)
        )
        ''')
        print("Tabla solved_problems creada")
        
        # Tabla de whitelist de correos
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS public.email_whitelist (
            id SERIAL PRIMARY KEY,
            email VARCHAR(100) UNIQUE NOT NULL,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            notes TEXT
        )
        ''')
        print("Tabla email_whitelist creada")
        
        # Verificar que las tablas existen
        cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
        tables = cursor.fetchall()
        print("\nTablas existentes en esquema 'public':")
        for table in tables:
            print(f" - {table[0]}")
        
        # Verificar que podemos hacer consultas a las tablas
        print("\nVerificando acceso a tablas:")
        try:
            cursor.execute("SELECT COUNT(*) FROM public.users")
            count = cursor.fetchone()[0]
            print(f"Total de usuarios: {count}")
        except Exception as e:
            print(f"Error al consultar tabla users: {e}")
        
        # Cerrar conexión
        cursor.close()
        conn.close()
        
        print("\nInicialización de PostgreSQL completada con éxito")
        
    except Exception as e:
        print(f"ERROR al inicializar PostgreSQL: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    setup_postgres() 