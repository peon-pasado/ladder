import sqlite3
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from app.config import DATABASE_URL, DB_TYPE, DATABASE_PATH

# Inicializar tablas inmediatamente
if DB_TYPE == 'postgresql':
    try:
        print("INICIALIZANDO TABLAS DE POSTGRESQL DESDE app/db.py")
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # Crear tablas básicas si no existen
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            password_hash VARCHAR(200) NOT NULL,
            rating INTEGER DEFAULT 1500
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS baekjoon_accounts (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id),
            baekjoon_username VARCHAR(50) NOT NULL,
            added_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, baekjoon_username)
        )
        ''')
        
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
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS email_whitelist (
            id SERIAL PRIMARY KEY,
            email VARCHAR(100) UNIQUE NOT NULL,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            notes TEXT
        )
        ''')
        
        conn.commit()
        
        # Verificar tablas
        cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
        tables = cursor.fetchall()
        print("Tablas PostgreSQL creadas:")
        for table in tables:
            print(f" - {table[0]}")
        
        cursor.close()
        conn.close()
        print("TABLAS INICIALIZADAS CORRECTAMENTE")
        
    except Exception as e:
        print(f"ERROR al inicializar tablas PostgreSQL: {e}")

class Database:
    """
    Clase para gestionar las conexiones y operaciones de base de datos.
    Soporta tanto SQLite como PostgreSQL según la configuración.
    """
    
    @staticmethod
    def get_connection(dict_cursor=True):
        """
        Obtiene una conexión a la base de datos según la configuración.
        
        Args:
            dict_cursor: Si es True, devuelve filas como diccionarios
            
        Returns:
            Una conexión a la base de datos
        """
        if DB_TYPE == 'postgresql':
            # Conexión a PostgreSQL
            try:
                if dict_cursor:
                    print(f"Conectando a PostgreSQL con URL: {DATABASE_URL}")
                    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
                else:
                    return psycopg2.connect(DATABASE_URL)
            except Exception as e:
                print(f"Error de conexión a PostgreSQL: {e}")
                print(f"URL: {DATABASE_URL}")
                raise
        else:
            # Conexión a SQLite
            print(f"Conectando a SQLite en: {DATABASE_PATH}")
            conn = sqlite3.connect(DATABASE_PATH)
            if dict_cursor:
                conn.row_factory = sqlite3.Row
            return conn
    
    @staticmethod
    def execute_query(query, params=None, fetchone=False, commit=False, dict_cursor=True):
        """
        Ejecuta una consulta en la base de datos.
        
        Args:
            query: Consulta SQL a ejecutar
            params: Parámetros para la consulta
            fetchone: Si es True, devuelve solo la primera fila
            commit: Si es True, realiza commit de los cambios
            dict_cursor: Si es True, devuelve filas como diccionarios
            
        Returns:
            El resultado de la consulta o None si es un commit
        """
        conn = Database.get_connection(dict_cursor)
        cursor = conn.cursor()
        
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            if commit:
                conn.commit()
                # Para SQLite, obtener lastrowid si está disponible
                last_id = getattr(cursor, 'lastrowid', None)
                affected = cursor.rowcount
                cursor.close()
                conn.close()
                return {"lastrowid": last_id, "rowcount": affected}
            elif fetchone:
                result = cursor.fetchone()
                cursor.close()
                conn.close()
                return result
            else:
                result = cursor.fetchall()
                cursor.close()
                conn.close()
                return result
        except Exception as e:
            print(f"Error en la consulta: {e}")
            print(f"Query: {query}")
            if params:
                print(f"Params: {params}")
            conn.close()
            raise e
    
    @staticmethod
    def table_exists(table_name):
        """
        Verifica si una tabla existe en la base de datos.
        
        Args:
            table_name: Nombre de la tabla a verificar
            
        Returns:
            Boolean: True si la tabla existe, False en caso contrario
        """
        if DB_TYPE == 'postgresql':
            query = "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = %s)"
            result = Database.execute_query(query, (table_name,), fetchone=True)
            return result['exists'] if result else False
        else:
            query = "SELECT name FROM sqlite_master WHERE type='table' AND name=?"
            result = Database.execute_query(query, (table_name,), fetchone=True)
            return result is not None 