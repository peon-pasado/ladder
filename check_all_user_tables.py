import psycopg2

# Conexión a la base de datos
DATABASE_URL = "postgresql://ladder_db_user:6FCOPInpMsKIazgN7WbdXd1dzsUwZVmv@dpg-d01m3rruibrs73aurmt0-a.virginia-postgres.render.com/ladder_db"
conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

# Usuarios a buscar
search_users = ["hhs2003", "cegax"]

print("BÚSQUEDA EXHAUSTIVA DE USUARIOS EN TODAS LAS TABLAS")
print("==================================================")

# 1. Listar todas las tablas en la base de datos
cur.execute("""
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public'
ORDER BY table_name
""")
tables = cur.fetchall()
print(f"Tablas en la base de datos: {len(tables)}")
for table in tables:
    print(f"  - {table[0]}")

# 2. Buscar usuarios en todas las columnas de tipo texto en todas las tablas
print("\nBuscando usuarios en todas las tablas...")
for search_user in search_users:
    print(f"\n=== BÚSQUEDA DE '{search_user}' ===")
    found = False
    
    for table in tables:
        table_name = table[0]
        
        # Obtener columnas de texto para esta tabla
        cur.execute("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = %s
        AND (data_type LIKE 'char%%' OR data_type LIKE 'varchar%%' OR data_type LIKE 'text')
        """, (table_name,))
        
        text_columns = cur.fetchall()
        
        # Buscar en cada columna de texto
        for column in text_columns:
            column_name = column[0]
            
            try:
                query = f"SELECT * FROM {table_name} WHERE {column_name} LIKE %s"
                cur.execute(query, (f"%{search_user}%",))
                matches = cur.fetchall()
                
                if matches:
                    found = True
                    print(f"✅ Encontrado en tabla '{table_name}', columna '{column_name}': {len(matches)} coincidencias")
                    
                    # Mostrar las primeras 3 coincidencias
                    if len(matches) > 0:
                        cols = [desc[0] for desc in cur.description]
                        print(f"  Primeras coincidencias:")
                        for i, match in enumerate(matches[:3]):
                            match_dict = dict(zip(cols, match))
                            print(f"  {i+1}. {match_dict}")
            except:
                # Ignorar errores (algunas consultas pueden fallar)
                pass
    
    if not found:
        print(f"❌ No se encontró '{search_user}' en ninguna tabla/columna de texto")

# 3. Buscar específicamente en las tablas principales
print("\n=== BÚSQUEDA EN TABLAS PRINCIPALES ===")
main_tables = ["users", "baekjoon_accounts", "ladder_problems"]

for table in main_tables:
    print(f"\nTabla: {table}")
    
    # Obtener todas las filas
    try:
        cur.execute(f"SELECT * FROM {table} LIMIT 100")
        rows = cur.fetchall()
        cols = [desc[0] for desc in cur.description]
        
        print(f"Columnas: {', '.join(cols)}")
        print(f"Total filas: {len(rows)}")
        
        # Mostrar algunas filas
        if len(rows) > 0:
            print("Primeras 5 filas:")
            for i, row in enumerate(rows[:5]):
                row_dict = dict(zip(cols, row))
                print(f"  {i+1}. {row_dict}")
    except Exception as e:
        print(f"Error al consultar tabla {table}: {str(e)}")

# 4. Contar cuentas de Baekjoon
print("\n=== CUENTAS BAEKJOON ===")
cur.execute("SELECT baekjoon_username FROM baekjoon_accounts")
accounts = cur.fetchall()
print(f"Total: {len(accounts)} cuentas")
for account in accounts:
    print(f"  - {account[0]}")

# 5. Contar usuarios en ladder_problems (por si hay inconsistencias)
print("\n=== USUARIOS EN LADDER_PROBLEMS ===")
cur.execute("SELECT DISTINCT baekjoon_username FROM ladder_problems")
ladder_users = cur.fetchall()
print(f"Total: {len(ladder_users)} usuarios")
for user in ladder_users:
    print(f"  - {user[0]}")

# Cerrar conexión
conn.close() 