#!/usr/bin/env python
import psycopg2

# URL de la base de datos
DATABASE_URL = "postgresql://ladder_db_user:6FCOPInpMsKIazgN7WbdXd1dzsUwZVmv@dpg-d01m3rruibrs73aurmt0-a.virginia-postgres.render.com/ladder_db"

print("Verificando estructura de la base de datos...")
print(f"Conectando a PostgreSQL con URL: {DATABASE_URL}")

try:
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    # Obtener la estructura de la tabla ladder_problems
    cursor.execute("""
    SELECT column_name, data_type, character_maximum_length
    FROM information_schema.columns
    WHERE table_name = 'ladder_problems'
    ORDER BY ordinal_position;
    """)
    
    columns = cursor.fetchall()
    
    print("\n=== Estructura de la tabla ladder_problems ===")
    print(f"{'Columna':<20} | {'Tipo':<15} | {'Longitud'}")
    print("-" * 50)
    
    for column in columns:
        length = str(column[2]) if column[2] is not None else ""
        print(f"{column[0]:<20} | {column[1]:<15} | {length}")
    
    # Verificar si existe la columna revealed_at
    has_revealed_at = any(column[0] == 'revealed_at' for column in columns)
    
    if not has_revealed_at:
        print("\n⚠️ La columna revealed_at no existe en la tabla ladder_problems")
        
        # Preguntar si queremos añadir la columna
        if "--add" in __import__("sys").argv:
            print("\nAñadiendo columna revealed_at a la tabla ladder_problems...")
            
            cursor.execute("""
            ALTER TABLE ladder_problems
            ADD COLUMN revealed_at TIMESTAMP;
            """)
            
            conn.commit()
            print("✅ Columna revealed_at añadida correctamente")
    else:
        print("\n✅ La columna revealed_at existe en la tabla ladder_problems")
    
    # Verificar otras tablas relevantes
    print("\n=== Tablas en la base de datos ===")
    cursor.execute("""
    SELECT table_name
    FROM information_schema.tables
    WHERE table_schema = 'public'
    ORDER BY table_name;
    """)
    
    tables = cursor.fetchall()
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
        count = cursor.fetchone()[0]
        print(f"{table[0]:<20} | {count} registros")
    
    conn.close()
    
except Exception as e:
    print(f"ERROR: {str(e)}")
    try:
        conn.close()
    except:
        pass 