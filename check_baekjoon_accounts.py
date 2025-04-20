import psycopg2

# Conexión a la base de datos
DATABASE_URL = "postgresql://ladder_db_user:6FCOPInpMsKIazgN7WbdXd1dzsUwZVmv@dpg-d01m3rruibrs73aurmt0-a.virginia-postgres.render.com/ladder_db"
conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

print("Listando todas las cuentas de Baekjoon en el sistema...\n")

# Listar todas las cuentas de Baekjoon
cur.execute("SELECT id, user_id, baekjoon_username FROM baekjoon_accounts ORDER BY id")
accounts = cur.fetchall()
if accounts:
    print(f"Total: {len(accounts)} cuentas de Baekjoon")
    print("\nLista completa de cuentas:")
    print(f"{'ID':<5} | {'User ID':<8} | {'Baekjoon Username'}")
    print("-" * 40)
    for account in accounts:
        print(f"{account[0]:<5} | {account[1]:<8} | {account[2]}")
    
    # Buscar cuentas que puedan parecerse a hhs2003
    print("\nBúsqueda de cuentas similares a 'hhs2003':")
    encontrado = False
    for account in accounts:
        if 'hhs' in account[2].lower() or '2003' in account[2]:
            print(f"Posible coincidencia: {account[2]} (ID: {account[0]}, User ID: {account[1]})")
            encontrado = True
    
    if not encontrado:
        print("No se encontraron cuentas similares a 'hhs2003'")
else:
    print("No hay cuentas de Baekjoon registradas en el sistema")

# Verificar usuarios del sistema que podrían agregar esta cuenta
print("\nUsuarios del sistema (potenciales para agregar la cuenta 'hhs2003'):")
cur.execute("SELECT id, username FROM users ORDER BY id")
users = cur.fetchall()
if users:
    for user in users:
        print(f"ID: {user[0]}, Username: {user[1]}")
else:
    print("No hay usuarios en el sistema")

# Cerrar conexión
conn.close()

print("\nPara agregar la cuenta 'hhs2003' al sistema, necesitas:")
print("1. Un usuario existente en el sistema (tabla 'users')")
print("2. Ejecutar una consulta SQL para insertar la nueva cuenta Baekjoon")
print("3. Inicializar el ladder para esta cuenta nueva") 