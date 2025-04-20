#!/usr/bin/env python
import psycopg2
from datetime import datetime, timedelta

# URL de la base de datos
DATABASE_URL = "postgresql://ladder_db_user:6FCOPInpMsKIazgN7WbdXd1dzsUwZVmv@dpg-d01m3rruibrs73aurmt0-a.virginia-postgres.render.com/ladder_db"

problem_id = "21065"
user_baekjoon = "admin_baekjoon"  # Usando la cuenta disponible en vez de "fischer"
position = 1

print(f"Agregando el problema {problem_id} como el primer problema (current) en el ladder de usuario {user_baekjoon}...")
print(f"Conectando a PostgreSQL con URL: {DATABASE_URL}")

try:
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    # 0. Mostrar todas las cuentas disponibles
    cursor.execute("SELECT baekjoon_username, user_id FROM baekjoon_accounts")
    accounts = cursor.fetchall()
    
    if accounts:
        print("\nCuentas disponibles:")
        for account in accounts:
            print(f"- {account[0]} (user_id: {account[1]})")
    
    # 1. Verificar si el problema existe
    cursor.execute("SELECT problem_id, problem_title FROM problems WHERE problem_id = %s", (problem_id,))
    problem = cursor.fetchone()
    
    if not problem:
        print(f"❌ Error: El problema {problem_id} no existe en la base de datos")
        conn.close()
        exit(1)
    
    problem_title = problem[1]
    print(f"✅ Problema encontrado: {problem_id} - {problem_title}")
    
    # 2. Verificar si existe el usuario
    cursor.execute("SELECT ba.user_id, u.username FROM baekjoon_accounts ba JOIN users u ON ba.user_id = u.id WHERE ba.baekjoon_username = %s", (user_baekjoon,))
    user = cursor.fetchone()
    
    if not user:
        print(f"❌ Error: No se encontró la cuenta de Baekjoon '{user_baekjoon}'")
        conn.close()
        exit(1)
    
    user_id = user[0]
    username = user[1]
    print(f"✅ Usuario encontrado: {username} (ID: {user_id})")
    
    # 3. Desmarcar cualquier problema actual en el ladder del usuario
    cursor.execute("""
    UPDATE ladder_problems 
    SET state = 'hidden' 
    WHERE baekjoon_username = %s AND state = 'current'
    """, (user_baekjoon,))
    
    unmarked = cursor.rowcount
    if unmarked > 0:
        print(f"✅ {unmarked} problemas desmarcados como current")
    
    # 4. Verificar si el problema ya existe en el ladder
    cursor.execute("""
    SELECT id, state FROM ladder_problems 
    WHERE baekjoon_username = %s AND problem_id = %s
    """, (user_baekjoon, problem_id))
    
    existing = cursor.fetchone()
    
    if existing:
        # Si ya existe, actualizarlo a current
        cursor.execute("""
        UPDATE ladder_problems 
        SET state = 'current', position = %s, revealed_at = %s
        WHERE id = %s
        """, (position, datetime.now() + timedelta(hours=6), existing[0]))
        
        print(f"✅ Problema {problem_id} actualizado a estado 'current', posición {position}")
    else:
        # Si no existe, insertarlo
        cursor.execute("""
        INSERT INTO ladder_problems 
        (baekjoon_username, position, problem_id, problem_title, state, revealed_at)
        VALUES (%s, %s, %s, %s, 'current', %s)
        """, (user_baekjoon, position, problem_id, problem_title, datetime.now() + timedelta(hours=6)))
        
        print(f"✅ Problema {problem_id} agregado como 'current' en posición {position}")
    
    # 5. Verificar el estado del ladder
    cursor.execute("""
    SELECT id, position, problem_id, problem_title, state, revealed_at 
    FROM ladder_problems
    WHERE baekjoon_username = %s
    ORDER BY position
    """, (user_baekjoon,))
    
    ladder = cursor.fetchall()
    
    print(f"\nLadder actualizado para {user_baekjoon}:")
    print(f"{'ID':<5} | {'Pos':<5} | {'Problem ID':<10} | {'Estado':<10} | {'Título'}")
    print("-" * 80)
    
    for p in ladder:
        print(f"{p[0]:<5} | {p[1]:<5} | {p[2]:<10} | {p[4]:<10} | {p[3]}")
    
    conn.commit()
    conn.close()
    
    print("\n✨ ¡Problema agregado con éxito al ladder del usuario!")
    
except Exception as e:
    print(f"ERROR: {str(e)}")
    try:
        conn.rollback()
        conn.close()
    except:
        pass 