import sqlite3
import os
import shutil
from app.config import DATABASE_PATH

def migrate_to_persistent():
    """
    Migra la base de datos actual a la ubicación configurada en DATABASE_PATH
    """
    local_db = 'app.db'
    
    # Verificar si existe la base de datos local
    if not os.path.exists(local_db):
        print(f"No se encuentra la base de datos local '{local_db}'.")
        return

    # Para desarrollo local, si DATABASE_PATH apunta a /data, usar un directorio local simulado
    target_path = DATABASE_PATH
    if '/data' in DATABASE_PATH:
        # Crear un directorio local para simular el volumen persistente
        local_data_dir = os.path.join(os.getcwd(), 'data_local')
        if not os.path.exists(local_data_dir):
            os.makedirs(local_data_dir)
        target_path = os.path.join(local_data_dir, 'app.db')
        print(f"Entorno local detectado. Usando {target_path} en lugar de {DATABASE_PATH}")
    
    # Si source y target son el mismo archivo, no hacer nada
    if os.path.abspath(local_db) == os.path.abspath(target_path):
        print(f"La base de datos origen y destino son la misma: {local_db}")
        print("No es necesario realizar la migración.")
        return

    # Verificar si ya existe la base de datos en el volumen persistente
    if os.path.exists(target_path):
        backup_path = f"{target_path}.bak"
        print(f"La base de datos {target_path} ya existe. Creando backup en {backup_path}")
        shutil.copy2(target_path, backup_path)
    
    # Asegurarse de que el directorio del volumen existe
    db_dir = os.path.dirname(target_path)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir)
    
    # Copiar la base de datos local al volumen persistente
    print(f"Migrando base de datos de {local_db} a {target_path}")
    shutil.copy2(local_db, target_path)
    
    # Verificar que la operación fue exitosa
    if os.path.exists(target_path):
        print(f"Migración completada con éxito.")
        print(f"NOTA: La base de datos local '{local_db}' no se ha eliminado.")
        print(f"      Si todo funciona correctamente, puede eliminarla manualmente.")
    else:
        print(f"Error: No se pudo migrar la base de datos al destino.")

if __name__ == '__main__':
    migrate_to_persistent() 