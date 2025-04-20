import psycopg2

# Conexión a la base de datos
DATABASE_URL = "postgresql://ladder_db_user:6FCOPInpMsKIazgN7WbdXd1dzsUwZVmv@dpg-d01m3rruibrs73aurmt0-a.virginia-postgres.render.com/ladder_db"
conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

# 1. Contar total de problemas
cur.execute("SELECT COUNT(*) FROM problems")
total_problems = cur.fetchone()[0]
print(f"Total de problemas en la base de datos: {total_problems}")

# 2. Ver algunos problemas recientes
print("\nÚltimos 10 problemas añadidos:")
cur.execute("""
SELECT problem_id, problem_title, tier, level 
FROM problems 
ORDER BY problem_id DESC 
LIMIT 10
""")
recent_problems = cur.fetchall()
for prob in recent_problems:
    print(f"ID: {prob[0]}, Título: {prob[1]}, Tier: {prob[2]}, Level: {prob[3]}")

# 3. Contar problemas por nivel
print("\nDistribución de problemas por nivel:")
cur.execute("""
SELECT level, COUNT(*) 
FROM problems 
WHERE level IS NOT NULL 
GROUP BY level 
ORDER BY level
""")
level_distribution = cur.fetchall()
for level in level_distribution:
    print(f"Nivel {level[0]}: {level[1]} problemas")

# 4. Buscar un problema específico (21065)
print("\nBuscando el problema 21065:")
cur.execute("SELECT * FROM problems WHERE problem_id = '21065'")
problem_21065 = cur.fetchone()
if problem_21065:
    cols = [desc[0] for desc in cur.description]
    problem_dict = dict(zip(cols, problem_21065))
    print("✅ Problema encontrado:")
    for key, value in problem_dict.items():
        print(f"  {key}: {value}")
else:
    print("❌ El problema 21065 no existe en la base de datos")

# Cerrar conexión
conn.close() 