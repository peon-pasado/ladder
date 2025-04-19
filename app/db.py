import sqlite3
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from app.config import DATABASE_URL, DB_TYPE, DATABASE_PATH

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
                    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
                    # Establecer explícitamente el esquema público
                    cursor = conn.cursor()
                    cursor.execute("SET search_path TO public")
                    conn.commit()
                    cursor.close()
                    return conn
                else:
                    conn = psycopg2.connect(DATABASE_URL)
                    # Establecer explícitamente el esquema público
                    cursor = conn.cursor()
                    cursor.execute("SET search_path TO public")
                    conn.commit()
                    cursor.close()
                    return conn
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
        # Si es PostgreSQL, modificar las consultas para usar el esquema 'public'
        if DB_TYPE == 'postgresql':
            # Reemplazar referencias a tablas para incluir el esquema público
            tables = ['users', 'baekjoon_accounts', 'ladder_problems', 'solved_problems', 'email_whitelist']
            for table in tables:
                query = query.replace(f' {table} ', f' public.{table} ')
                if query.startswith(f'SELECT * FROM {table}'):
                    query = query.replace(f'SELECT * FROM {table}', f'SELECT * FROM public.{table}')
                if query.startswith(f'INSERT INTO {table}'):
                    query = query.replace(f'INSERT INTO {table}', f'INSERT INTO public.{table}')
                if query.startswith(f'UPDATE {table}'):
                    query = query.replace(f'UPDATE {table}', f'UPDATE public.{table}')
                if query.startswith(f'DELETE FROM {table}'):
                    query = query.replace(f'DELETE FROM {table}', f'DELETE FROM public.{table}')
        
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