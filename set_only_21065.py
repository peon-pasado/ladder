#!/usr/bin/env python
import psycopg2
from datetime import datetime, timedelta

# URL de la base de datos
DATABASE_URL = "postgresql://ladder_db_user:6FCOPInpMsKIazgN7WbdXd1dzsUwZVmv@dpg-d01m3rruibrs73aurmt0-a.virginia-postgres.render.com/ladder_db"

baekjoon_username = "fischer"  # Solo para esta cuenta
problem_id = "21065"  # El problema que queremos asignar
position = 1

print(f"RESET COMPLETO: ASIGNANDO SOLO EL PROBLEMA {problem_id} A {baekjoon_username}")
print(f"Conectando a PostgreSQL con URL: {DATABASE_URL}")

try:
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    # 1. ELIMINACIÓN TOTAL DEL LADDER ACTUAL
    cursor.execute("DELETE FROM ladder_problems WHERE baekjoon_username = %s", (baekjoon_username,))
    deleted = cursor.rowcount
    print(f"✅ PASO 1: Se eliminaron {deleted} problemas del ladder")
    
    # 2. VERIFICAR QUE EL PROBLEMA EXISTE
    cursor.execute("SELECT problem_id, problem_title FROM problems WHERE problem_id = %s", (problem_id,))
    problem = cursor.fetchone()
    
    if not problem:
        print(f"❌ Error: El problema {problem_id} no existe en la base de datos")
        conn.close()
        exit(1)
    
    problem_title = problem[1]
    print(f"✅ PASO 2: Problema encontrado: {problem_id} - {problem_title}")
    
    # 3. INSERTAR EL PROBLEMA COMO CURRENT
    cursor.execute("""
    INSERT INTO ladder_problems 
    (baekjoon_username, position, problem_id, problem_title, state, revealed_at)
    VALUES (%s, %s, %s, %s, 'current', %s)
    """, (baekjoon_username, position, problem_id, problem_title, datetime.now() - timedelta(hours=1)))
    
    print(f"✅ PASO 3: Problema {problem_id} agregado como 'current' en posición {position}")
    
    # 4. VERIFICAR QUE ES EL ÚNICO PROBLEMA
    cursor.execute("SELECT COUNT(*) FROM ladder_problems WHERE baekjoon_username = %s", (baekjoon_username,))
    count = cursor.fetchone()[0]
    
    if count == 1:
        print(f"✅ PASO 4: Verificado - {count} problema en el ladder (correcto)")
    else:
        print(f"⚠️ PASO 4: Alerta - {count} problemas en el ladder (debería ser solo 1)")
    
    # 5. MOSTRAR EL LADDER FINAL
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
    
    print("\n✨ RESET COMPLETO ✨")
    print(f"AHORA EL PROBLEMA {problem_id} ES EL ÚNICO EN TU LADDER.")
    print("Por favor, sigue estos pasos:")
    print("1. Cierra completamente la aplicación web")
    print("2. Borra el caché del navegador")
    print("3. Reinicia el navegador")
    print("4. Accede nuevamente a la aplicación")
    print("5. Verifica que aparezca el problema 21065")
    
except Exception as e:
    print(f"ERROR: {str(e)}")
    try:
        conn.rollback()
        conn.close()
    except:
        pass 