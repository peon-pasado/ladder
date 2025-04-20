import psycopg2

# Conexión a la base de datos
DATABASE_URL = "postgresql://ladder_db_user:6FCOPInpMsKIazgN7WbdXd1dzsUwZVmv@dpg-d01m3rruibrs73aurmt0-a.virginia-postgres.render.com/ladder_db"
conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

print("Listando todos los usuarios en la base de datos...\n")

# 1. Listar todos los usuarios en la tabla users
print("Usuarios en la tabla 'users':")
cur.execute("SELECT id, username, email, rating FROM users ORDER BY id")
users = cur.fetchall()
if users:
    print(f"Total: {len(users)} usuarios")
    for user in users:
        print(f"ID: {user[0]}, Username: {user[1]}, Email: {user[2]}, Rating: {user[3]}")
else:
    print("No hay usuarios en la tabla 'users'")

# 2. Listar todas las cuentas Baekjoon
print("\nCuentas en la tabla 'baekjoon_accounts':")
cur.execute("SELECT id, user_id, baekjoon_username FROM baekjoon_accounts ORDER BY id")
accounts = cur.fetchall()
if accounts:
    print(f"Total: {len(accounts)} cuentas")
    for account in accounts:
        print(f"ID: {account[0]}, User ID: {account[1]}, Baekjoon Username: {account[2]}")
else:
    print("No hay cuentas en la tabla 'baekjoon_accounts'")

# 3. Listar usuarios únicos en ladder_problems
print("\nUsuarios únicos en la tabla 'ladder_problems':")
cur.execute("SELECT DISTINCT baekjoon_username FROM ladder_problems ORDER BY baekjoon_username")
ladder_users = cur.fetchall()
if ladder_users:
    print(f"Total: {len(ladder_users)} usuarios con problemas asignados")
    for user in ladder_users:
        cur.execute("SELECT COUNT(*) FROM ladder_problems WHERE baekjoon_username = %s", (user[0],))
        count = cur.fetchone()[0]
        print(f"Usuario: {user[0]} - Problemas: {count}")
else:
    print("No hay usuarios con problemas asignados")

# Cerrar conexión
conn.close() 