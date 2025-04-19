import os
import shutil
import sqlite3

def migrate_db_location():
    """
    Migra la base de datos desde /data/app.db (ruta antigua) a /data/db/app.db (nueva ruta)
    """
    old_path = '/data/app.db'
    new_path = '/data/db/app.db'
    
    print(f"Verificando si es necesario migrar la base de datos...")
    
    # Verificar si existe la base de datos en la ruta antigua
    if not os.path.exists(old_path):
        print(f"No hay base de datos en la ruta antigua ({old_path}), no es necesario migrar.")
        return
    
    # Crear el directorio de destino si no existe
    new_dir = os.path.dirname(new_path)
    if not os.path.exists(new_dir):
        try:
            os.makedirs(new_dir)
            print(f"Directorio de destino creado: {new_dir}")
        except Exception as e:
            print(f"Error al crear directorio {new_dir}: {e}")
            return
    
    # Verificar si existe una base de datos en la nueva ruta
    if os.path.exists(new_path):
        backup_path = f"{new_path}.bak"
        print(f"Ya existe una base de datos en {new_path}. Haciendo backup en {backup_path}")
        try:
            shutil.copy2(new_path, backup_path)
        except Exception as e:
            print(f"Error al hacer backup: {e}")
    
    # Copiar la base de datos a la nueva ubicación
    try:
        print(f"Copiando base de datos de {old_path} a {new_path}")
        shutil.copy2(old_path, new_path)
        print("Base de datos migrada correctamente")
    except Exception as e:
        print(f"Error al migrar la base de datos: {e}")
        return
    
    # Verificar que la nueva base de datos funciona correctamente
    try:
        conn = sqlite3.connect(new_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        conn.close()
        print(f"Verificación exitosa - tablas encontradas: {len(tables)}")
    except Exception as e:
        print(f"Error al verificar la nueva base de datos: {e}")
        return
    
    print("Migración completada con éxito.")

if __name__ == '__main__':
    migrate_db_location() 