import psycopg2
import sqlite3
import os

# Verificar si hay una base de datos SQLite
sqlite_path = 'app.db'
has_sqlite = os.path.exists(sqlite_path)

print("DIAGNÓSTICO DE MÚLTIPLES FUENTES DE DATOS")
print("========================================")

print(f"¿Existe base de datos SQLite (app.db)? {has_sqlite}")

# Verificar datos en PostgreSQL
print("\n=== DATOS EN POSTGRESQL ===")
try:
    pg_url = "postgresql://ladder_db_user:6FCOPInpMsKIazgN7WbdXd1dzsUwZVmv@dpg-d01m3rruibrs73aurmt0-a.virginia-postgres.render.com/ladder_db"
    pg_conn = psycopg2.connect(pg_url)
    pg_cur = pg_conn.cursor()
    
    # Verificar usuarios
    pg_cur.execute("SELECT id, username FROM users")
    pg_users = pg_cur.fetchall()
    print(f"Usuarios en PostgreSQL: {len(pg_users)}")
    for user in pg_users:
        print(f"  - ID: {user[0]}, Username: {user[1]}")
    
    # Verificar cuentas Baekjoon
    pg_cur.execute("SELECT id, user_id, baekjoon_username FROM baekjoon_accounts")
    pg_accounts = pg_cur.fetchall()
    print(f"\nCuentas Baekjoon en PostgreSQL: {len(pg_accounts)}")
    for account in pg_accounts:
        print(f"  - ID: {account[0]}, User ID: {account[1]}, Username: {account[2]}")
    
    pg_conn.close()
except Exception as e:
    print(f"Error al conectar a PostgreSQL: {str(e)}")

# Verificar datos en SQLite si existe
if has_sqlite:
    print("\n=== DATOS EN SQLITE ===")
    try:
        sqlite_conn = sqlite3.connect(sqlite_path)
        sqlite_conn.row_factory = sqlite3.Row
        sqlite_cur = sqlite_conn.cursor()
        
        # Verificar si existen las tablas
        sqlite_cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in sqlite_cur.fetchall()]
        print(f"Tablas en SQLite: {', '.join(tables)}")
        
        # Verificar usuarios si existe la tabla
        if 'users' in tables:
            sqlite_cur.execute("SELECT id, username FROM users")
            sqlite_users = sqlite_cur.fetchall()
            print(f"\nUsuarios en SQLite: {len(sqlite_users)}")
            for user in sqlite_users:
                print(f"  - ID: {user['id']}, Username: {user['username']}")
        
        # Verificar cuentas Baekjoon si existe la tabla
        if 'baekjoon_accounts' in tables:
            sqlite_cur.execute("SELECT id, user_id, baekjoon_username FROM baekjoon_accounts")
            sqlite_accounts = sqlite_cur.fetchall()
            print(f"\nCuentas Baekjoon en SQLite: {len(sqlite_accounts)}")
            for account in sqlite_accounts:
                print(f"  - ID: {account['id']}, User ID: {account['user_id']}, Username: {account['baekjoon_username']}")
                
            # Buscar específicamente hhs2003 y cegax
            search_terms = ['hhs2003', 'cegax']
            for term in search_terms:
                sqlite_cur.execute("SELECT * FROM baekjoon_accounts WHERE baekjoon_username LIKE ?", (f"%{term}%",))
                matches = sqlite_cur.fetchall()
                if matches:
                    print(f"\nCoincidencias para '{term}' en SQLite:")
                    for match in matches:
                        print(f"  - ID: {match['id']}, User ID: {match['user_id']}, Username: {match['baekjoon_username']}")
        
        sqlite_conn.close()
    except Exception as e:
        print(f"Error al verificar SQLite: {str(e)}")

# Comprobar posible conflicto en código
print("\n=== ANÁLISIS DE POSIBLE CAUSA DEL PROBLEMA ===")
print("Al revisar el código del archivo app/models/baekjoon_account.py:")
print("⚠️ El método get_accounts_by_user_id usa SQLite para obtener las cuentas, no PostgreSQL")
print("⚠️ Esto podría explicar por qué ves cuentas en la interfaz que no existen en PostgreSQL")
print("\nPara solucionar esto, la aplicación debería:")
print("1. Usar consistentemente PostgreSQL para todos los accesos a la base de datos")
print("2. Sincronizar los datos entre SQLite y PostgreSQL si usa ambas")
print("3. Actualizar las funciones en app/models para que usen la misma fuente de datos") 