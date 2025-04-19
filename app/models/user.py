from flask_login import UserMixin
import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash
from app.config import DATABASE_PATH

class User(UserMixin):
    def __init__(self, id, username, email, password_hash, rating=1500):
        self.id = id
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.rating = rating
    
    @staticmethod
    def get(user_id):
        conn = sqlite3.connect(DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        user_data = cursor.fetchone()
        conn.close()
        
        if user_data:
            # Check if 'rating' column exists in the result
            rating = 1500
            try:
                rating = user_data['rating']
            except (IndexError, KeyError):
                # If rating column doesn't exist, use default
                pass
                
            return User(
                id=user_data['id'],
                username=user_data['username'],
                email=user_data['email'],
                password_hash=user_data['password_hash'],
                rating=rating
            )
        return None
    
    @staticmethod
    def get_by_username(username):
        conn = sqlite3.connect(DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        user_data = cursor.fetchone()
        conn.close()
        
        if user_data:
            # Check if 'rating' column exists in the result
            rating = 1500
            try:
                rating = user_data['rating']
            except (IndexError, KeyError):
                # If rating column doesn't exist, use default
                pass
                
            return User(
                id=user_data['id'],
                username=user_data['username'],
                email=user_data['email'],
                password_hash=user_data['password_hash'],
                rating=rating
            )
        return None
    
    @staticmethod
    def create(username, email, password):
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        password_hash = generate_password_hash(password)
        
        cursor.execute(
            "INSERT INTO users (username, email, password_hash, rating) VALUES (?, ?, ?, ?)",
            (username, email, password_hash, 1500)
        )
        
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()
        
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
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Obtener el rating actual
        cursor.execute("SELECT rating FROM users WHERE id = ?", (user_id,))
        current_rating = cursor.fetchone()[0]
        
        # Calcular el nuevo rating (nunca menor que 0)
        new_rating = max(0, current_rating + delta_rating)
        
        # Actualizar el rating en la base de datos
        cursor.execute(
            "UPDATE users SET rating = ? WHERE id = ?", 
            (new_rating, user_id)
        )
        
        conn.commit()
        conn.close()
        
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
        conn = sqlite3.connect(DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM email_whitelist WHERE email = ?", (email,))
        result = cursor.fetchone()
        
        conn.close()
        
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
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "INSERT INTO email_whitelist (email, notes) VALUES (?, ?)",
                (email, notes)
            )
            conn.commit()
            success = True
        except sqlite3.IntegrityError:
            # El correo ya existe en la whitelist
            success = False
        finally:
            conn.close()
            
        return success
        
    @staticmethod
    def remove_email_from_whitelist(email):
        """
        Elimina un correo electrónico de la whitelist
        
        Args:
            email: Correo electrónico a eliminar
            
        Returns:
            Boolean: True si se eliminó correctamente, False si no existía
        """
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM email_whitelist WHERE email = ?", (email,))
        rows_affected = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        return rows_affected > 0
        
    @staticmethod
    def get_whitelist():
        """
        Obtiene todos los correos electrónicos en la whitelist
        
        Returns:
            List: Lista de diccionarios con los correos en la whitelist
        """
        conn = sqlite3.connect(DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM email_whitelist ORDER BY added_at DESC")
        results = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        
        return results 