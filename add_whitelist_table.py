import sqlite3
import os
import sys
from app.config import DATABASE_PATH

def add_whitelist_table():
    print(f"Verificando tabla whitelist en: {DATABASE_PATH}")
    
    # Asegurarse de que el directorio existe
    db_dir = os.path.dirname(DATABASE_PATH)
    if db_dir:
        try:
            if not os.path.exists(db_dir):
                os.makedirs(db_dir, exist_ok=True)
                print(f"Directorio creado: {db_dir}")
            
            # Verificar permisos
            if not os.access(db_dir, os.W_OK):
                print(f"¡ADVERTENCIA! No se tienen permisos de escritura en {db_dir}")
                try:
                    # Intentar corregir
                    os.chmod(db_dir, 0o777)
                    print(f"Permisos actualizados para {db_dir}")
                except Exception as e:
                    print(f"Error al cambiar permisos: {e}")
        except Exception as e:
            print(f"Error al crear directorio {db_dir}: {e}")
            sys.exit(1)
    
    try:
        conn = sqlite3.connect(DATABASE_PATH)
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
    except Exception as e:
        print(f"Error al crear tabla whitelist: {e}")
        sys.exit(1)

if __name__ == '__main__':
    add_whitelist_table() 