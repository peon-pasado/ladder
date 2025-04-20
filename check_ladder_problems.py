import psycopg2

# Conexión a la base de datos
DATABASE_URL = "postgresql://ladder_db_user:6FCOPInpMsKIazgN7WbdXd1dzsUwZVmv@dpg-d01m3rruibrs73aurmt0-a.virginia-postgres.render.com/ladder_db"
conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

# 1. Ver todos los usuarios con ladder
print("USUARIOS CON LADDER:")
print("=" * 50)
cur.execute("""
SELECT DISTINCT baekjoon_username 
FROM ladder_problems 
ORDER BY baekjoon_username
""")
users_with_ladder = cur.fetchall()

if not users_with_ladder:
    print("No hay usuarios con ladder")
else:
    for i, user in enumerate(users_with_ladder):
        username = user[0]
        print(f"\n{i+1}. Usuario: {username}")
        print("-" * 50)
        
        # Contar problemas para este usuario
        cur.execute("SELECT COUNT(*) FROM ladder_problems WHERE baekjoon_username = %s", (username,))
        problem_count = cur.fetchone()[0]
        print(f"Total de problemas: {problem_count}")
        
        # Verificar problemas 'current'
        cur.execute("""
        SELECT COUNT(*) 
        FROM ladder_problems 
        WHERE baekjoon_username = %s AND state = 'current'
        """, (username,))
        current_count = cur.fetchone()[0]
        print(f"Problemas 'current': {current_count}")
        
        if current_count > 0:
            cur.execute("""
            SELECT id, position, problem_id, problem_title, state, revealed_at
            FROM ladder_problems 
            WHERE baekjoon_username = %s AND state = 'current'
            ORDER BY position
            """, (username,))
            current_problems = cur.fetchall()
            
            print("Problemas actuales:")
            for prob in current_problems:
                print(f"  - ID: {prob[0]}, Pos: {prob[1]}, Problem: {prob[2]}, Título: {prob[3]}, Revelado: {prob[5]}")
        
        # Mostrar primeros 5 problemas
        cur.execute("""
        SELECT id, position, problem_id, problem_title, state
        FROM ladder_problems 
        WHERE baekjoon_username = %s
        ORDER BY position
        LIMIT 5
        """, (username,))
        first_problems = cur.fetchall()
        
        print("Primeros problemas en el ladder:")
        for prob in first_problems:
            print(f"  - ID: {prob[0]}, Pos: {prob[1]}, Problem: {prob[2]}, Título: {prob[3]}, Estado: {prob[4]}")
        
        # Mostrar estados de los problemas (conteo)
        cur.execute("""
        SELECT state, COUNT(*) 
        FROM ladder_problems 
        WHERE baekjoon_username = %s
        GROUP BY state
        ORDER BY COUNT(*) DESC
        """, (username,))
        state_counts = cur.fetchall()
        
        print("Conteo por estado:")
        for state in state_counts:
            print(f"  - {state[0]}: {state[1]} problemas")

# Cerrar conexión
conn.close() 