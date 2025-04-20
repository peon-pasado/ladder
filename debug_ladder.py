#!/usr/bin/env python
import psycopg2
from datetime import datetime, timedelta
import json

# URL de la base de datos
DATABASE_URL = "postgresql://ladder_db_user:6FCOPInpMsKIazgN7WbdXd1dzsUwZVmv@dpg-d01m3rruibrs73aurmt0-a.virginia-postgres.render.com/ladder_db"

baekjoon_username = "fischer"
problem_id = "21065"  # El problema que queremos mantener

print(f"DIAGNÓSTICO PROFUNDO DEL LADDER PARA: {baekjoon_username}")
print(f"Conectando a PostgreSQL con URL: {DATABASE_URL}")

try:
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    # 1. Verificar usuarios y cuentas de Baekjoon
    print("\n1. USUARIOS Y CUENTAS DE BAEKJOON:")
    cursor.execute("SELECT u.id, u.username, ba.baekjoon_username FROM users u LEFT JOIN baekjoon_accounts ba ON u.id = ba.user_id")
    users = cursor.fetchall()
    for user in users:
        print(f"Usuario: {user[1]} (ID: {user[0]}), Cuenta Baekjoon: {user[2] if user[2] else 'NO TIENE'}")
    
    # 2. Verificar el estado actual del ladder
    print("\n2. ESTADO ACTUAL DEL LADDER PARA FISCHER:")
    cursor.execute("""
    SELECT id, position, problem_id, problem_title, state, revealed_at 
    FROM ladder_problems
    WHERE baekjoon_username = %s
    ORDER BY position
    """, (baekjoon_username,))
    
    ladder = cursor.fetchall()
    if not ladder:
        print("¡No hay problemas en el ladder!")
    else:
        for p in ladder:
            print(f"ID: {p[0]}, Pos: {p[1]}, Problem: {p[2]}, Título: {p[3]}, Estado: {p[4]}, Revelado: {p[5]}")
    
    # 3. Verificar problemas en la base de datos
    print("\n3. PROBLEMAS EN LA BASE DE DATOS:")
    cursor.execute("SELECT problem_id, problem_title FROM problems WHERE problem_id IN ('21065', '21041', '21067')")
    problems = cursor.fetchall()
    for problem in problems:
        print(f"Problema: {problem[0]} - {problem[1]}")
    
    # 4. Verificar si existen reglas o triggers especiales
    print("\n4. VERIFICANDO REGLAS O TRIGGERS DEL SISTEMA:")
    cursor.execute("""
    SELECT event_object_table, trigger_name, event_manipulation 
    FROM information_schema.triggers 
    WHERE event_object_schema = 'public'
    """)
    triggers = cursor.fetchall()
    if not triggers:
        print("No hay triggers en la base de datos.")
    else:
        for trigger in triggers:
            print(f"Trigger: {trigger[1]} en tabla {trigger[0]} para evento {trigger[2]}")
    
    # 5. Buscar alguna función o procedimiento almacenado que pueda estar modificando el ladder
    print("\n5. VERIFICANDO FUNCIONES Y PROCEDIMIENTOS:")
    cursor.execute("""
    SELECT routine_name, routine_type 
    FROM information_schema.routines 
    WHERE routine_schema = 'public'
    """)
    routines = cursor.fetchall()
    if not routines:
        print("No hay funciones o procedimientos almacenados.")
    else:
        for routine in routines:
            print(f"{routine[1]}: {routine[0]}")
    
    # 6. Solución: reiniciar completamente el ladder y asignar el problema correcto
    print("\n6. REINICIANDO EL LADDER (SOLUCIÓN FORZADA):")
    
    # 6.1 Eliminar TODOS los problemas existentes
    cursor.execute("DELETE FROM ladder_problems WHERE baekjoon_username = %s", (baekjoon_username,))
    deleted = cursor.rowcount
    print(f"Se eliminaron {deleted} problemas del ladder.")
    
    # 6.2 Verificar si el problema existe
    cursor.execute("SELECT problem_id, problem_title FROM problems WHERE problem_id = %s", (problem_id,))
    problem = cursor.fetchone()
    if not problem:
        print(f"❌ Error: El problema {problem_id} no existe en la base de datos")
        # Buscar problemas similares
        cursor.execute("SELECT problem_id, problem_title FROM problems ORDER BY problem_id LIMIT 10")
        available = cursor.fetchall()
        print("Problemas disponibles:")
        for p in available:
            print(f"- {p[0]}: {p[1]}")
    else:
        # 6.3 Insertar el problema de forma forzada
        problem_title = problem[1]
        position = 1
        current_time = datetime.now()
        
        cursor.execute("""
        INSERT INTO ladder_problems 
        (baekjoon_username, position, problem_id, problem_title, state, revealed_at)
        VALUES (%s, %s, %s, %s, 'current', %s)
        """, (baekjoon_username, position, problem_id, problem_title, current_time))
        
        print(f"✅ Problema {problem_id} agregado como 'current' en posición {position}")
        print(f"   Título: {problem_title}")
        print(f"   Tiempo: {current_time}")
    
    # 7. Verificar el estado final del ladder
    print("\n7. ESTADO FINAL DEL LADDER:")
    cursor.execute("""
    SELECT id, position, problem_id, problem_title, state, revealed_at 
    FROM ladder_problems
    WHERE baekjoon_username = %s
    ORDER BY position
    """, (baekjoon_username,))
    
    final_ladder = cursor.fetchall()
    if not final_ladder:
        print("¡El ladder está vacío! Algo salió mal.")
    else:
        for p in final_ladder:
            print(f"ID: {p[0]}, Pos: {p[1]}, Problem: {p[2]}, Título: {p[3]}, Estado: {p[4]}, Revelado: {p[5]}")
    
    conn.commit()
    conn.close()
    
    print("\n✨ DIAGNÓSTICO COMPLETADO ✨")
    print("Reinicia la aplicación web e intenta acceder al ladder nuevamente.")
    print("Si el problema persiste, es posible que la aplicación esté ejecutando código adicional")
    print("que modifica el ladder al iniciar sesión o al acceder a él.")
    
except Exception as e:
    print(f"ERROR: {str(e)}")
    try:
        conn.rollback()
        conn.close()
    except:
        pass 