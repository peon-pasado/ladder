import psycopg2

# Conexión a la base de datos
DATABASE_URL = "postgresql://ladder_db_user:6FCOPInpMsKIazgN7WbdXd1dzsUwZVmv@dpg-d01m3rruibrs73aurmt0-a.virginia-postgres.render.com/ladder_db"
conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

print("Buscando al usuario 'hhs2003' en la base de datos...\n")

# 1. Buscar en la tabla users
print("Búsqueda en tabla 'users':")
cur.execute("SELECT id, username, email, rating FROM users WHERE username LIKE %s", ('%hhs2003%',))
users = cur.fetchall()
if users:
    for user in users:
        print(f"ID: {user[0]}, Username: {user[1]}, Email: {user[2]}, Rating: {user[3]}")
else:
    print("No se encontró el usuario en la tabla 'users'")

# 2. Buscar en la tabla baekjoon_accounts
print("\nBúsqueda en tabla 'baekjoon_accounts':")
cur.execute("SELECT id, user_id, baekjoon_username FROM baekjoon_accounts WHERE baekjoon_username LIKE %s", ('%hhs2003%',))
accounts = cur.fetchall()
if accounts:
    for account in accounts:
        print(f"ID: {account[0]}, User ID: {account[1]}, Baekjoon Username: {account[2]}")
else:
    print("No se encontró el usuario en la tabla 'baekjoon_accounts'")

# 3. Buscar en la tabla ladder_problems
print("\nBúsqueda en tabla 'ladder_problems':")
cur.execute("SELECT COUNT(*) FROM ladder_problems WHERE baekjoon_username LIKE %s", ('%hhs2003%',))
problem_count = cur.fetchone()[0]
if problem_count > 0:
    print(f"Se encontraron {problem_count} problemas en ladder_problems para el usuario")
    
    # Mostrar los problemas
    cur.execute("""
    SELECT id, position, problem_id, problem_title, state, revealed_at 
    FROM ladder_problems 
    WHERE baekjoon_username LIKE %s
    ORDER BY position
    """, ('%hhs2003%',))
    
    problems = cur.fetchall()
    for prob in problems:
        print(f"ID: {prob[0]}, Pos: {prob[1]}, Problem: {prob[2]}, Título: {prob[3]}, Estado: {prob[4]}")
else:
    print("No se encontraron problemas en el ladder para este usuario")

# Verificar la existencia de la cuenta
if accounts:
    user_id = accounts[0][1]
    print(f"\nEl usuario hhs2003 (ID: {user_id}) existe en el sistema")
    
    # Verificar si tiene un ladder vacío
    if problem_count == 0:
        print("El usuario existe pero no tiene problemas en su ladder.")
        print("Para inicializar el ladder, se puede usar la función 'reset_ladder' en la aplicación.")
        
        # Verificar problemas disponibles
        cur.execute("SELECT COUNT(*) FROM problems")
        available_problems = cur.fetchone()[0]
        print(f"Hay {available_problems} problemas disponibles para asignar al ladder.")
else:
    print("\nNo se encontró el usuario 'hhs2003' en ninguna tabla relevante.")

# Cerrar conexión
conn.close() 