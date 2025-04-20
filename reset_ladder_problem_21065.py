#!/usr/bin/env python
import psycopg2
from datetime import datetime, timedelta

# URL de la base de datos
DATABASE_URL = "postgresql://ladder_db_user:6FCOPInpMsKIazgN7WbdXd1dzsUwZVmv@dpg-d01m3rruibrs73aurmt0-a.virginia-postgres.render.com/ladder_db"

problem_id = "21065"  # El problema que queremos asignar
baekjoon_username = "fischer"
position = 1

print(f"REINICIANDO LADDER: Asignando SOLO el problema {problem_id} al ladder de {baekjoon_username}...")
print(f"Conectando a PostgreSQL con URL: {DATABASE_URL}")

try:
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    # Verificar si el problema existe
    cursor.execute("SELECT problem_id, problem_title FROM problems WHERE problem_id = %s", (problem_id,))
    problem = cursor.fetchone()
    
    if not problem:
        print(f"❌ Error: El problema {problem_id} no existe en la base de datos")
        # Intentar encontrar problemas similares
        cursor.execute("SELECT problem_id, problem_title FROM problems WHERE problem_id LIKE %s LIMIT 5", (f"{problem_id[:3]}%",))
        similar_problems = cursor.fetchall()
        if similar_problems:
            print("Problemas similares encontrados:")
            for p in similar_problems:
                print(f"- {p[0]}: {p[1]}")
        conn.close()
        exit(1)
    
    problem_title = problem[1]
    print(f"✅ Problema encontrado: {problem_id} - {problem_title}")
    
    # Eliminar TODOS los problemas existentes en el ladder
    cursor.execute("""
    DELETE FROM ladder_problems 
    WHERE baekjoon_username = %s
    """, (baekjoon_username,))
    
    deleted = cursor.rowcount
    if deleted > 0:
        print(f"✅ {deleted} problemas eliminados del ladder")
    
    # Insertar el problema correcto como el único problema actual
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
    
    print(f"\nLadder actualizado para {baekjoon_username}:")
    print(f"{'ID':<5} | {'Pos':<5} | {'Problem ID':<10} | {'Estado':<10} | {'Título'}")
    print("-" * 80)
    
    for p in ladder:
        print(f"{p[0]:<5} | {p[1]:<5} | {p[2]:<10} | {p[4]:<10} | {p[3]}")
    
    conn.commit()
    conn.close()
    
    print("\n✨ ¡Ladder reiniciado correctamente! Ahora solo tiene el problema 21065 como actual.")
    print("Reinicia la aplicación web para ver el cambio.")
    
except Exception as e:
    print(f"ERROR: {str(e)}")
    try:
        conn.rollback()
        conn.close()
    except:
        pass 