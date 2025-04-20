#!/usr/bin/env python
import psycopg2
from datetime import datetime, timedelta

# URL de la base de datos
DATABASE_URL = "postgresql://ladder_db_user:6FCOPInpMsKIazgN7WbdXd1dzsUwZVmv@dpg-d01m3rruibrs73aurmt0-a.virginia-postgres.render.com/ladder_db"

baekjoon_username = "fischer"  # Solo para esta cuenta
problem_id = "20397"  # El problema que el usuario ve actualmente
position = 1

print(f"ASIGNANDO EL PROBLEMA ACTUAL {problem_id} a {baekjoon_username}")
print(f"Conectando a PostgreSQL con URL: {DATABASE_URL}")

try:
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    # Verificar que es la cuenta correcta
    cursor.execute("""
    SELECT ba.user_id, u.username 
    FROM baekjoon_accounts ba
    JOIN users u ON ba.user_id = u.id
    WHERE ba.baekjoon_username = %s
    """, (baekjoon_username,))
    
    user_info = cursor.fetchone()
    if not user_info:
        print(f"❌ Error: No se encontró la cuenta Baekjoon '{baekjoon_username}'")
        conn.close()
        exit(1)
    
    print(f"✅ Cuenta confirmada: {baekjoon_username} (Usuario: {user_info[1]}, ID: {user_info[0]})")
    
    # Verificar si el problema existe en la base de datos
    cursor.execute("SELECT problem_id, problem_title FROM problems WHERE problem_id = %s", (problem_id,))
    problem = cursor.fetchone()
    
    if not problem:
        print(f"❌ Error: El problema {problem_id} no existe en la base de datos")
        # Buscar problemas similares
        cursor.execute("SELECT problem_id, problem_title FROM problems WHERE problem_id LIKE %s LIMIT 5", (problem_id[:2] + "%",))
        similar = cursor.fetchall()
        if similar:
            print("Problemas similares encontrados:")
            for p in similar:
                print(f"- {p[0]}: {p[1]}")
        conn.close()
        exit(1)
    
    problem_title = problem[1]
    print(f"✅ Problema encontrado: {problem_id} - {problem_title}")
    
    # Eliminar TODOS los problemas del ladder para empezar limpio
    cursor.execute("DELETE FROM ladder_problems WHERE baekjoon_username = %s", (baekjoon_username,))
    deleted = cursor.rowcount
    print(f"✅ Se eliminaron {deleted} problemas del ladder para empezar limpio")
    
    # Insertar el problema como current con revealed_at = ahora (ya revelado)
    cursor.execute("""
    INSERT INTO ladder_problems 
    (baekjoon_username, position, problem_id, problem_title, state, revealed_at)
    VALUES (%s, %s, %s, %s, 'current', %s)
    """, (baekjoon_username, position, problem_id, problem_title, datetime.now() - timedelta(hours=1)))  # Ya revelado
    
    print(f"✅ Problema {problem_id} agregado como 'current' en posición {position}")
    
    # Verificar el estado actual del ladder
    cursor.execute("""
    SELECT id, position, problem_id, problem_title, state, revealed_at 
    FROM ladder_problems
    WHERE baekjoon_username = %s
    ORDER BY position
    """, (baekjoon_username,))
    
    ladder = cursor.fetchall()
    print(f"\nLadder actual para {baekjoon_username}:")
    for p in ladder:
        print(f"ID: {p[0]}, Pos: {p[1]}, Problema: {p[2]}, Título: {p[3]}, Estado: {p[4]}, Revelado: {p[5]}")
    
    conn.commit()
    conn.close()
    
    print("\n✨ ASIGNACIÓN COMPLETADA ✨")
    print(f"AHORA EL PROBLEMA {problem_id} ES EL ÚNICO EN TU LADDER.")
    print("Este cambio debería hacer que el problema 20397 aparezca en la aplicación.")
    print("Reinicia la aplicación y verifica que el problema 20397 aparezca correctamente.")
    
except Exception as e:
    print(f"ERROR: {str(e)}")
    try:
        conn.rollback()
        conn.close()
    except:
        pass 