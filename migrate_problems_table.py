import sqlite3

def migrate_problems_table():
    """
    Migra la tabla 'problems' para añadir los campos adicionales necesarios
    para almacenar información de Solved.ac
    """
    conn = sqlite3.connect('app.db')
    cursor = conn.cursor()
    
    # Verificar la estructura actual de la tabla
    cursor.execute("PRAGMA table_info(problems)")
    columns = [col[1] for col in cursor.fetchall()]
    
    print("Estructura actual de la tabla 'problems':")
    print(columns)
    
    # Añadir columnas faltantes
    columns_to_add = {
        'tier': 'INTEGER DEFAULT NULL',
        'tags': 'TEXT DEFAULT NULL',
        'solved_count': 'INTEGER DEFAULT 0',
        'level': 'INTEGER DEFAULT NULL',
        'accepted_user_count': 'INTEGER DEFAULT 0',
        'average_tries': 'REAL DEFAULT 0.0'
    }
    
    for column, type_def in columns_to_add.items():
        if column not in columns:
            print(f"Añadiendo columna '{column}'...")
            cursor.execute(f"ALTER TABLE problems ADD COLUMN {column} {type_def}")
    
    # Verificar que se hayan añadido todas las columnas
    cursor.execute("PRAGMA table_info(problems)")
    updated_columns = [col[1] for col in cursor.fetchall()]
    
    print("Estructura actualizada de la tabla 'problems':")
    print(updated_columns)
    
    conn.commit()
    conn.close()
    print("Migración completada con éxito")

if __name__ == "__main__":
    migrate_problems_table() 