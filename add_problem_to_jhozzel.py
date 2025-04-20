#!/usr/bin/env python
import psycopg2
from datetime import datetime, timedelta

# URL de la base de datos
DATABASE_URL = "postgresql://ladder_db_user:6FCOPInpMsKIazgN7WbdXd1dzsUwZVmv@dpg-d01m3rruibrs73aurmt0-a.virginia-postgres.render.com/ladder_db"

problem_id = "21065"
user_id = 2  # ID de JhoZzel
position = 1

print(f"Agregando problema {problem_id} al ladder de JhoZzel...")
print(f"Conectando a PostgreSQL con URL: {DATABASE_URL}")

try:
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    # Verificar si el usuario existe
    cursor.execute("SELECT username FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    
    if not user:
        print(f"❌ Error: No se encontró usuario con ID {user_id}")
        conn.close()
        exit(1)
    
    username = user[0]
    print(f"✅ Usuario: {username} (ID: {user_id})")
    
    # Obtener o crear cuenta de Baekjoon
    cursor.execute("SELECT baekjoon_username FROM baekjoon_accounts WHERE user_id = %s", (user_id,))
    baekjoon_account = cursor.fetchone()
    
    if not baekjoon_account:
        # Si no existe cuenta, crear una usando el ID del usuario como nombre
        cursor.execute("INSERT INTO baekjoon_accounts (user_id, baekjoon_username) VALUES (%s, %s)", 
                      (user_id, str(user_id)))
        baekjoon_username = str(user_id)
        print(f"✅ Creada cuenta de Baekjoon para usuario {username}: {baekjoon_username}")
    else:
        baekjoon_username = baekjoon_account[0]
        print(f"✅ Cuenta de Baekjoon encontrada: {baekjoon_username}")
    
    # Verificar si el problema existe
    cursor.execute("SELECT problem_id, problem_title FROM problems WHERE problem_id = %s", (problem_id,))
    problem = cursor.fetchone()
    
    if not problem:
        print(f"❌ Error: El problema {problem_id} no existe en la base de datos")
        conn.close()
        exit(1)
    
    problem_title = problem[1]
    print(f"✅ Problema encontrado: {problem_id} - {problem_title}")
    
    # Desmarcar cualquier problema actual en el ladder del usuario
    cursor.execute("""
    UPDATE ladder_problems 
    SET state = 'hidden' 
    WHERE baekjoon_username = %s AND state = 'current'
    """, (baekjoon_username,))
    
    unmarked = cursor.rowcount
    if unmarked > 0:
        print(f"✅ {unmarked} problemas desmarcados como current")
    
    # Verificar si el problema ya existe en el ladder
    cursor.execute("""
    SELECT id, state FROM ladder_problems 
    WHERE baekjoon_username = %s AND problem_id = %s
    """, (baekjoon_username, problem_id))
    
    existing = cursor.fetchone()
    
    if existing:
        # Si ya existe, actualizarlo a current
        cursor.execute("""
        UPDATE ladder_problems 
        SET state = 'current', position = %s, revealed_at = %s
        WHERE id = %s
        """, (position, datetime.now(), existing[0]))
        
        print(f"✅ Problema {problem_id} actualizado a estado 'current', posición {position}")
    else:
        # Si no existe, insertarlo
        cursor.execute("""
        INSERT INTO ladder_problems 
        (baekjoon_username, position, problem_id, problem_title, state, revealed_at)
        VALUES (%s, %s, %s, %s, 'current', %s)
        """, (baekjoon_username, position, problem_id, problem_title, datetime.now()))
        
        print(f"✅ Problema {problem_id} agregado como 'current' en posición {position}")
    
    # Verificar el estado del ladder
    cursor.execute("""
    SELECT id, position, problem_id, problem_title, state, revealed_at 
    FROM ladder_problems
    WHERE baekjoon_username = %s
    ORDER BY position
    """, (baekjoon_username,))
    
    ladder = cursor.fetchall()
    
    print(f"\nLadder actualizado para usuario {username} (ID: {user_id}):")
    print(f"{'ID':<5} | {'Pos':<5} | {'Problem ID':<10} | {'Estado':<10} | {'Título'}")
    print("-" * 80)
    
    for p in ladder:
        print(f"{p[0]:<5} | {p[1]:<5} | {p[2]:<10} | {p[4]:<10} | {p[3]}")
    
    conn.commit()
    conn.close()
    
    print("\n✨ ¡Problema agregado con éxito al ladder del usuario JhoZzel!")
    
except Exception as e:
    print(f"ERROR: {str(e)}")
    try:
        conn.rollback()
        conn.close()
    except:
        pass 