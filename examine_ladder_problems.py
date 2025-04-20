import psycopg2

# Conexión a la base de datos
conn = psycopg2.connect('postgresql://ladder_db_user:6FCOPInpMsKIazgN7WbdXd1dzsUwZVmv@dpg-d01m3rruibrs73aurmt0-a.virginia-postgres.render.com/ladder_db')
cur = conn.cursor()

# Examinar la estructura de la tabla
print("Estructura de la tabla ladder_problems:")
cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'ladder_problems' ORDER BY ordinal_position")
columns = cur.fetchall()
for col in columns:
    print(f"{col[0]}: {col[1]}")

# Ver los primeros registros
print("\nPrimeros 5 registros de ladder_problems:")
cur.execute("SELECT * FROM ladder_problems LIMIT 5")
cols = [desc[0] for desc in cur.description]
rows = cur.fetchall()
for row in rows:
    print(dict(zip(cols, row)))

# Contar registros por usuario
print("\nNúmero de problemas por usuario:")
cur.execute("SELECT baekjoon_username, COUNT(*) FROM ladder_problems GROUP BY baekjoon_username")
for user_count in cur.fetchall():
    print(f"Usuario: {user_count[0]} - Problemas: {user_count[1]}")

# Examinar si hay problemas marcados como 'current'
print("\nProblemas marcados como current:")
cur.execute("SELECT * FROM ladder_problems WHERE state = 'current'")
current_problems = cur.fetchall()
if current_problems:
    for prob in current_problems:
        print(dict(zip(cols, prob)))
else:
    print("No hay problemas marcados como current")

# Ver todos los usuarios únicos
print("\nUsuarios en la tabla ladder_problems:")
cur.execute("SELECT DISTINCT baekjoon_username FROM ladder_problems")
users = cur.fetchall()
for user in users:
    print(user[0])

# Cerrar conexión
conn.close() 