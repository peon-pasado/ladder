import sqlite3
import requests
import re
from datetime import datetime
import os
from app.config import DB_TYPE, DATABASE_URL

# Importar psycopg2 solo si se va a usar PostgreSQL
if DB_TYPE == 'postgresql':
    import psycopg2

class BaekjoonAccount:
    def __init__(self, id, user_id, baekjoon_username, added_on):
        self.id = id
        self.user_id = user_id
        self.baekjoon_username = baekjoon_username
        self.added_on = added_on
    
    @staticmethod
    def get_accounts_by_user_id(user_id):
        from app.db import Database
        
        if DB_TYPE == 'postgresql':
            query = "SELECT * FROM baekjoon_accounts WHERE user_id = %s ORDER BY added_on DESC"
        else:
            query = "SELECT * FROM baekjoon_accounts WHERE user_id = ? ORDER BY added_on DESC"
        
        results = Database.execute_query(query, (user_id,))
        
        accounts = []
        for account_data in results:
            accounts.append(BaekjoonAccount(
                id=account_data[0],          # id
                user_id=account_data[1],     # user_id
                baekjoon_username=account_data[2],  # baekjoon_username
                added_on=account_data[3]     # added_on
            ))
        
        return accounts
    
    @staticmethod
    def add_account(user_id, baekjoon_username):
        from app.db import Database
        
        # Primero verificar si la cuenta existe usando la API
        if not BaekjoonAccount.verify_account(baekjoon_username):
            return False, "La cuenta de Baekjoon no existe"
        
        try:
            if DB_TYPE == 'postgresql':
                query = "INSERT INTO baekjoon_accounts (user_id, baekjoon_username, added_on) VALUES (%s, %s, %s) RETURNING id"
            else:
                query = "INSERT INTO baekjoon_accounts (user_id, baekjoon_username, added_on) VALUES (?, ?, ?)"
            
            result = Database.execute_query(
                query,
                (user_id, baekjoon_username, datetime.now()),
                commit=True
            )
            
            if DB_TYPE == 'postgresql' and result:
                new_id = result[0][0]
            else:
                # Para SQLite, obtener el último ID insertado
                new_id = Database.execute_query("SELECT last_insert_rowid()")[0][0]
            
            return True, new_id
        except Exception as e:
            return False, f"Error al agregar la cuenta: {str(e)}"
    
    @staticmethod
    def verify_account(username):
        """
        Verificar si la cuenta existe directamente en la página de Baekjoon
        Este método es más preciso que usar la API de solved.ac, especialmente
        para cuentas nuevas.
        """
        try:
            direct_url = f"https://www.acmicpc.net/user/{username}"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(direct_url, headers=headers)
            
            if response.status_code == 200:
                # Si la página contiene mensajes de error específicos, el usuario no existe
                error_messages = [
                    "등록된 사용자가 없습니다",  # No registered user
                    "존재하지 않는 사용자입니다"  # User does not exist
                ]
                
                for error in error_messages:
                    if error in response.text:
                        return False
                
                # Verificar si se menciona el nombre de usuario en la página
                if username.lower() in response.text.lower():
                    return True
                    
                # Si no hay mensajes de error y llegamos hasta aquí, asumimos que el usuario existe
                return True
            
            return False
        except Exception:
            # En caso de cualquier error, asumimos que la cuenta no existe
            return False
    
    @staticmethod
    def delete_account(account_id, user_id):
        """Eliminar una cuenta de Baekjoon"""
        from app.db import Database
        
        if DB_TYPE == 'postgresql':
            query = "DELETE FROM baekjoon_accounts WHERE id = %s AND user_id = %s"
        else:
            query = "DELETE FROM baekjoon_accounts WHERE id = ? AND user_id = ?"
        
        Database.execute_query(query, (account_id, user_id), commit=True)
        return True 
        
    @staticmethod
    def check_problem_solved(username, problem_id, start_time=None, end_time=None):
        """
        Verifica si un usuario ha resuelto un problema específico en Baekjoon.
        Si se proporcionan start_time y end_time, intentará verificar si se resolvió en ese intervalo,
        aunque la API actual no proporciona esa información directamente.
        
        Args:
            username (str): Nombre de usuario de Baekjoon
            problem_id (str): ID del problema a verificar
            start_time (datetime, opcional): Tiempo de inicio del intervalo
            end_time (datetime, opcional): Tiempo de fin del intervalo
            
        Returns:
            tuple: (True/False, mensaje)
        """
        try:
            print(f"[DEBUG check_problem_solved] Verificando: username={username}, problem_id={problem_id}")
            
            # Usamos la API de solved.ac para verificar el problema resuelto
            # No verificamos primero si la cuenta existe porque si está en nuestra DB, asumimos que es válida
            api_url = f"https://solved.ac/api/v3/search/problem?query=solved_by:{username}+id:{problem_id}"
            
            print(f"[DEBUG check_problem_solved] Llamando a API: {api_url}")
            
            response = requests.get(api_url, timeout=10)
            
            print(f"[DEBUG check_problem_solved] Response status: {response.status_code}")
            
            if response.status_code == 404:
                # 404 puede significar que la cuenta no existe o que no hay resultados
                # Intentamos verificar si la cuenta existe
                if not BaekjoonAccount.verify_account(username):
                    return False, f"La cuenta de Baekjoon '{username}' no existe o no es accesible"
                return False, f"El usuario {username} no ha resuelto el problema {problem_id}"
            
            if response.status_code != 200:
                return False, f"Error al consultar la API de solved.ac (código {response.status_code}). Intenta de nuevo más tarde."
            
            data = response.json()
            
            print(f"[DEBUG check_problem_solved] API response count: {data.get('count', 0)}")
            
            # Verificamos si hay resultados
            if data.get('count', 0) > 0:
                # La API actual no proporciona la fecha de resolución, así que no podemos
                # verificar si fue resuelto en el intervalo de tiempo especificado
                if start_time and end_time:
                    return True, f"El usuario {username} ha resuelto el problema {problem_id}, pero no se puede determinar si fue dentro del intervalo especificado."
                return True, f"El usuario {username} ha resuelto el problema {problem_id}"
            else:
                return False, f"El usuario {username} no ha resuelto el problema {problem_id}"
            
        except requests.exceptions.Timeout:
            return False, "Timeout al consultar la API de solved.ac. Intenta de nuevo."
        except requests.exceptions.RequestException as e:
            return False, f"Error de red al verificar el problema: {str(e)}"
        except Exception as e:
            print(f"[ERROR check_problem_solved] Exception: {type(e).__name__}: {str(e)}")
            return False, f"Error al verificar el problema: {str(e)}" 