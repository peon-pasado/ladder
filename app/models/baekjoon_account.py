import sqlite3
import requests
import re
from datetime import datetime

class BaekjoonAccount:
    def __init__(self, id, user_id, baekjoon_username, added_on):
        self.id = id
        self.user_id = user_id
        self.baekjoon_username = baekjoon_username
        self.added_on = added_on
    
    @staticmethod
    def get_accounts_by_user_id(user_id):
        conn = sqlite3.connect('app.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT * FROM baekjoon_accounts WHERE user_id = ? ORDER BY added_on DESC",
            (user_id,)
        )
        
        accounts = []
        for account_data in cursor.fetchall():
            accounts.append(BaekjoonAccount(
                id=account_data['id'],
                user_id=account_data['user_id'],
                baekjoon_username=account_data['baekjoon_username'],
                added_on=account_data['added_on']
            ))
        
        conn.close()
        return accounts
    
    @staticmethod
    def add_account(user_id, baekjoon_username):
        # Primero verificar si la cuenta existe usando la API
        if not BaekjoonAccount.verify_account(baekjoon_username):
            return False, "La cuenta de Baekjoon no existe"
        
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            cursor.execute(
                "INSERT INTO baekjoon_accounts (user_id, baekjoon_username) VALUES (?, ?)",
                (user_id, baekjoon_username)
            )
            
            conn.commit()
            new_id = cursor.lastrowid
            conn.close()
            
            return True, new_id
        except sqlite3.IntegrityError:
            return False, "Ya tienes esta cuenta registrada"
    
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
        conn = sqlite3.connect('app.db')
        cursor = conn.cursor()
        
        cursor.execute(
            "DELETE FROM baekjoon_accounts WHERE id = ? AND user_id = ?",
            (account_id, user_id)
        )
        
        deleted = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return deleted 
        
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
            # Primero verificamos que la cuenta existe
            if not BaekjoonAccount.verify_account(username):
                return False, "La cuenta de Baekjoon no existe"
            
            # Usamos la API de solved.ac para verificar el problema resuelto
            api_url = f"https://solved.ac/api/v3/search/problem?query=solved_by:{username}+id:{problem_id}"
            response = requests.get(api_url)
            
            if response.status_code != 200:
                return False, f"Error al consultar la API: {response.status_code}"
            
            data = response.json()
            
            # Verificamos si hay resultados
            if data['count'] > 0:
                # La API actual no proporciona la fecha de resolución, así que no podemos
                # verificar si fue resuelto en el intervalo de tiempo especificado
                if start_time and end_time:
                    return True, f"El usuario {username} ha resuelto el problema {problem_id}, pero no se puede determinar si fue dentro del intervalo especificado."
                return True, f"El usuario {username} ha resuelto el problema {problem_id}"
            else:
                return False, f"El usuario {username} no ha resuelto el problema {problem_id}"
            
        except Exception as e:
            return False, f"Error al verificar el problema: {str(e)}" 