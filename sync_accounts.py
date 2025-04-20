import sqlite3
import psycopg2
from datetime import datetime

print("SINCRONIZANDO CUENTAS DE SQLITE A POSTGRESQL")
print("===========================================")

# Conexión a SQLite
sqlite_conn = sqlite3.connect('app.db')
sqlite_conn.row_factory = sqlite3.Row
sqlite_cur = sqlite_conn.cursor()

# Conexión a PostgreSQL
pg_url = "postgresql://ladder_db_user:6FCOPInpMsKIazgN7WbdXd1dzsUwZVmv@dpg-d01m3rruibrs73aurmt0-a.virginia-postgres.render.com/ladder_db"
pg_conn = psycopg2.connect(pg_url)
pg_cur = pg_conn.cursor()

# 1. Obtener todas las cuentas de SQLite
sqlite_cur.execute("SELECT user_id, baekjoon_username, added_on FROM baekjoon_accounts")
sqlite_accounts = sqlite_cur.fetchall()
print(f"Cuentas encontradas en SQLite: {len(sqlite_accounts)}")

# 2. Obtener todas las cuentas de PostgreSQL
pg_cur.execute("SELECT user_id, baekjoon_username FROM baekjoon_accounts")
pg_accounts = pg_cur.fetchall()
pg_usernames = [account[1] for account in pg_accounts]
print(f"Cuentas existentes en PostgreSQL: {len(pg_accounts)}")

# 3. Para cada cuenta en SQLite, verificar si ya existe en PostgreSQL
accounts_to_add = []
for account in sqlite_accounts:
    user_id = account['user_id']
    username = account['baekjoon_username']
    added_on = account['added_on'] if 'added_on' in account else datetime.now()
    
    if username not in pg_usernames:
        accounts_to_add.append((user_id, username, added_on))

print(f"Cuentas a agregar: {len(accounts_to_add)}")

# 4. Para las cuentas que buscamos específicamente, agregarlas manualmente
manual_accounts = [
    {'username': 'hhs2003', 'user_id': 1},  # Asociar a user_id 1 (admin)
    {'username': 'cegax', 'user_id': 1}     # Asociar a user_id 1 (admin)
]

for account in manual_accounts:
    username = account['username']
    user_id = account['user_id']
    
    if username not in pg_usernames:
        print(f"Agregando manualmente: {username} (user_id: {user_id})")
        pg_cur.execute(
            "INSERT INTO baekjoon_accounts (user_id, baekjoon_username, added_on) VALUES (%s, %s, %s)",
            (user_id, username, datetime.now())
        )
        pg_conn.commit()
        print(f"✅ Cuenta {username} agregada exitosamente")
    else:
        print(f"La cuenta {username} ya existe en PostgreSQL")

# 5. Mostrar las cuentas actualizadas
pg_cur.execute("SELECT id, user_id, baekjoon_username FROM baekjoon_accounts ORDER BY id")
updated_accounts = pg_cur.fetchall()
print("\nCuentas en PostgreSQL después de la sincronización:")
for account in updated_accounts:
    print(f"  - ID: {account[0]}, User ID: {account[1]}, Username: {account[2]}")

# 6. Verificar si las cuentas hhs2003 y cegax se agregaron correctamente
print("\nVerificando cuentas específicas:")
for username in ['hhs2003', 'cegax']:
    pg_cur.execute("SELECT id, user_id FROM baekjoon_accounts WHERE baekjoon_username = %s", (username,))
    account = pg_cur.fetchone()
    if account:
        print(f"✅ Cuenta {username} encontrada (ID: {account[0]}, User ID: {account[1]})")
    else:
        print(f"❌ Cuenta {username} NO encontrada")

# Cerrar conexiones
sqlite_conn.close()
pg_conn.close()

print("\nSincronización completada. Ahora deberías poder usar las cuentas en la aplicación.")
print("NOTA: Para una solución permanente, modifica el código de la aplicación para usar PostgreSQL en todas las operaciones.") 