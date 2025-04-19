import sqlite3
import os
from werkzeug.security import generate_password_hash
import getpass
from app.config import DATABASE_PATH

def create_admin_user():
    admin_username = 'admin'
    admin_email = input("Introduce el correo del administrador: ")
    admin_password = getpass.getpass("Introduce la contraseña del administrador: ")
    
    # Asegurarse de que el directorio existe
    db_dir = os.path.dirname(DATABASE_PATH)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir)
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Comprobar si la tabla de whitelist existe
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='email_whitelist'")
    whitelist_exists = cursor.fetchone()
    
    if not whitelist_exists:
        print("Creando tabla para la whitelist de correos...")
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS email_whitelist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            notes TEXT
        )
        ''')
        print("Tabla de whitelist de correos creada correctamente")
    
    # Añadir el correo del administrador a la whitelist
    try:
        cursor.execute(
            "INSERT INTO email_whitelist (email, notes) VALUES (?, ?)",
            (admin_email, "Usuario administrador")
        )
        print(f"Correo {admin_email} añadido a la whitelist")
    except sqlite3.IntegrityError:
        print(f"El correo {admin_email} ya estaba en la whitelist")
    
    # Comprobar si el usuario administrador ya existe
    cursor.execute("SELECT * FROM users WHERE username = ?", (admin_username,))
    admin_exists = cursor.fetchone()
    
    if admin_exists:
        print(f"El usuario '{admin_username}' ya existe")
    else:
        # Crear usuario administrador
        password_hash = generate_password_hash(admin_password)
        
        cursor.execute(
            "INSERT INTO users (username, email, password_hash, rating) VALUES (?, ?, ?, ?)",
            (admin_username, admin_email, password_hash, 1500)
        )
        print(f"Usuario administrador '{admin_username}' creado correctamente")
    
    conn.commit()
    conn.close()
    
    print("Proceso completado con éxito.")

if __name__ == '__main__':
    create_admin_user() 