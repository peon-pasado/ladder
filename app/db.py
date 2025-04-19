import psycopg2
from psycopg2.extras import RealDictCursor
import os
from app.config import DATABASE_URL

class Database:
    """
    Clase para gestionar las conexiones y operaciones de base de datos.
    Simplificada para usar PostgreSQL.
    """
    
    @staticmethod
    def get_connection(dict_cursor=True):
        """
        Obtiene una conexión a la base de datos PostgreSQL.
        
        Args:
            dict_cursor: Si es True, devuelve filas como diccionarios
            
        Returns:
            Una conexión a la base de datos
        """
        if dict_cursor:
            return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        else:
            return psycopg2.connect(DATABASE_URL)
    
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
                affected = cursor.rowcount
                cursor.close()
                conn.close()
                return {"lastrowid": None, "rowcount": affected}
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
        query = "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = %s)"
        result = Database.execute_query(query, (table_name,), fetchone=True)
        return result['exists'] if result else False 