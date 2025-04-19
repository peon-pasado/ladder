import sqlite3
import os

def add_whitelist_table():
    conn = sqlite3.connect('app.db')
    cursor = conn.cursor()
    
    # Verificar si la tabla whitelist ya existe
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='email_whitelist'")
    table_exists = cursor.fetchone()
    
    if not table_exists:
        print("Creando tabla para la whitelist de correos...")
        # Crear tabla para la whitelist de correos
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS email_whitelist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            notes TEXT
        )
        ''')
        print("Tabla de whitelist de correos creada correctamente")
    else:
        print("La tabla de whitelist de correos ya existe")
    
    # Guardar los cambios y cerrar la conexión
    conn.commit()
    conn.close()
    
    print("Base de datos actualizada con éxito.")

if __name__ == '__main__':
    add_whitelist_table() 