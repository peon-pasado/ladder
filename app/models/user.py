from flask_login import UserMixin
import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash
from app.config import DATABASE_URL, DB_TYPE
from app.db import Database
from app.utils.constants import Constants

class User(UserMixin):
    def __init__(self, id, username, email, password_hash, rating=None, is_admin=False):
        self.id = id
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.rating = rating if rating is not None else Constants.DEFAULT_USER_RATING
        self.is_admin = bool(is_admin)
    
    @staticmethod
    def get(user_id):
        query = "SELECT * FROM users WHERE id = %s" if DB_TYPE == 'postgresql' else "SELECT * FROM users WHERE id = ?"
        user_data = Database.execute_query(query, (user_id,), fetchone=True)
        
        if user_data:
            # Check if 'rating' column exists in the result
            rating = Constants.DEFAULT_USER_RATING
            is_admin = False
            try:
                rating = user_data['rating']
            except (IndexError, KeyError):
                pass
            
            try:
                is_admin = user_data['is_admin']
            except (IndexError, KeyError):
                pass
                
            return User(
                id=user_data['id'],
                username=user_data['username'],
                email=user_data['email'],
                password_hash=user_data['password_hash'],
                rating=rating,
                is_admin=is_admin
            )
        return None
    
    @staticmethod
    def get_by_username(username):
        query = "SELECT * FROM users WHERE username = %s" if DB_TYPE == 'postgresql' else "SELECT * FROM users WHERE username = ?"
        user_data = Database.execute_query(query, (username,), fetchone=True)
        
        if user_data:
            # Check if 'rating' column exists in the result
            rating = Constants.DEFAULT_USER_RATING
            is_admin = False
            try:
                rating = user_data['rating']
            except (IndexError, KeyError):
                pass
            
            try:
                is_admin = user_data['is_admin']
            except (IndexError, KeyError):
                pass
                
            return User(
                id=user_data['id'],
                username=user_data['username'],
                email=user_data['email'],
                password_hash=user_data['password_hash'],
                rating=rating,
                is_admin=is_admin
            )
        return None
    
    @staticmethod
    def create(username, email, password):
        password_hash = generate_password_hash(password)
        
        query = """
            INSERT INTO users (username, email, password_hash, rating) 
            VALUES (%s, %s, %s, %s)
        """ if DB_TYPE == 'postgresql' else """
            INSERT INTO users (username, email, password_hash, rating) 
            VALUES (?, ?, ?, ?)
        """
        
        result = Database.execute_query(
            query,
            (username, email, password_hash, Constants.DEFAULT_USER_RATING),
            commit=True
        )
        
        user_id = result['lastrowid']
        # En PostgreSQL, necesitamos obtener el ID generado de otra forma
        if DB_TYPE == 'postgresql':
            id_query = "SELECT id FROM users WHERE username = %s"
            user_data = Database.execute_query(id_query, (username,), fetchone=True)
            user_id = user_data['id'] if user_data else None
            
        return User.get(user_id)
    
    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    @staticmethod
    def update_rating(user_id, delta_rating):
        """
        Actualiza el rating de un usuario basado en el cambio calculado
        
        Args:
            user_id: ID del usuario
            delta_rating: Cambio en el rating (positivo o negativo)
        
        Returns:
            Nuevo rating del usuario
        """
        # Obtener el rating actual
        rating_query = "SELECT rating FROM users WHERE id = %s" if DB_TYPE == 'postgresql' else "SELECT rating FROM users WHERE id = ?"
        current_rating_data = Database.execute_query(rating_query, (user_id,), fetchone=True)
        
        print(f"[DEBUG User.update_rating] user_id={user_id}, current_rating_data={current_rating_data}")
        
        if not current_rating_data:
            print(f"[DEBUG User.update_rating] No rating data found for user {user_id}")
            return None
            
        current_rating = current_rating_data['rating']
        
        # Calcular el nuevo rating (nunca menor que 0)
        from app.utils.constants import Constants
        new_rating = max(Constants.MIN_USER_RATING, current_rating + delta_rating)
        
        print(f"[DEBUG User.update_rating] current_rating={current_rating}, delta_rating={delta_rating}, new_rating={new_rating}")
        
        # Actualizar el rating en la base de datos
        update_query = "UPDATE users SET rating = %s WHERE id = %s" if DB_TYPE == 'postgresql' else "UPDATE users SET rating = ? WHERE id = ?"
        result = Database.execute_query(
            update_query, 
            (new_rating, user_id),
            commit=True
        )
        
        print(f"[DEBUG User.update_rating] Update result: {result}")
        
        return new_rating
    
    @staticmethod
    def is_email_in_whitelist(email):
        """
        Verifica si un correo electrónico está en la whitelist
        
        Args:
            email: Correo electrónico a verificar
            
        Returns:
            Boolean: True si el correo está en la whitelist, False en caso contrario
        """
        query = "SELECT * FROM email_whitelist WHERE email = %s" if DB_TYPE == 'postgresql' else "SELECT * FROM email_whitelist WHERE email = ?"
        result = Database.execute_query(query, (email,), fetchone=True)
        
        return result is not None
        
    @staticmethod
    def add_email_to_whitelist(email, notes=None):
        """
        Añade un correo electrónico a la whitelist
        
        Args:
            email: Correo electrónico a añadir
            notes: Notas opcionales sobre este correo
            
        Returns:
            Boolean: True si se añadió correctamente, False si ya existía
        """
        try:
            query = """
                INSERT INTO email_whitelist (email, notes) 
                VALUES (%s, %s)
            """ if DB_TYPE == 'postgresql' else """
                INSERT INTO email_whitelist (email, notes) 
                VALUES (?, ?)
            """
            
            Database.execute_query(query, (email, notes), commit=True)
            return True
        except Exception:
            # Asumir que ya existe (violación de clave única)
            return False
        
    @staticmethod
    def remove_email_from_whitelist(email):
        """
        Elimina un correo electrónico de la whitelist
        
        Args:
            email: Correo electrónico a eliminar
            
        Returns:
            Boolean: True si se eliminó correctamente, False si no existía
        """
        query = "DELETE FROM email_whitelist WHERE email = %s" if DB_TYPE == 'postgresql' else "DELETE FROM email_whitelist WHERE email = ?"
        result = Database.execute_query(query, (email,), commit=True)
        
        return result['rowcount'] > 0
        
    @staticmethod
    def get_whitelist():
        """
        Obtiene todos los correos electrónicos en la whitelist
        
        Returns:
            List: Lista de diccionarios con los correos en la whitelist
        """
        query = "SELECT * FROM email_whitelist ORDER BY added_at DESC"
        results = Database.execute_query(query)
        
        # Convertir a lista de diccionarios si es necesario
        if DB_TYPE == 'sqlite':
            return [dict(row) for row in results]
        return results 