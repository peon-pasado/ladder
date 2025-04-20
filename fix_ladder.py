#!/usr/bin/env python
import os
import sys
import psycopg2
from datetime import datetime, timezone

# URL de la base de datos
DATABASE_URL = "postgresql://ladder_db_user:6FCOPInpMsKIazgN7WbdXd1dzsUwZVmv@dpg-d01m3rruibrs73aurmt0-a.virginia-postgres.render.com/ladder_db"

print(f"Conectando a PostgreSQL con URL: {DATABASE_URL}")

try:
    # Conectar a la base de datos
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    # Usuario y problema específico
    user_id = 1  # ID del usuario admin
    problem_id = '21065'  # El problema que el usuario mencionó
    
    # 1. Obtener información de la cuenta del usuario
    cursor.execute("SELECT baekjoon_username FROM baekjoon_accounts WHERE user_id = %s", (user_id,))
    account = cursor.fetchone()
    if not account:
        print(f"ERROR: Usuario con ID {user_id} no tiene cuenta Baekjoon asociada")
        sys.exit(1)
    
    baekjoon_username = account[0]
    print(f"Cuenta Baekjoon: {baekjoon_username}")
    
    # 2. Verificar que el problema existe en la tabla problems
    cursor.execute("SELECT problem_id, problem_title FROM problems WHERE problem_id = %s", (problem_id,))
    problem_info = cursor.fetchone()
    if not problem_info:
        print(f"ERROR: El problema {problem_id} no existe en la tabla 'problems'")
        sys.exit(1)
    
    problem_title = problem_info[1]
    print(f"Problema {problem_id} encontrado: {problem_title}")
    
    # 3. Limpiar el ladder actual (eliminar todos los problemas)
    print("\n=== REPARANDO LADDER ===")
    print("Eliminando problemas actuales del ladder...")
    
    cursor.execute("""
    DELETE FROM ladder_problems 
    WHERE baekjoon_username = %s
    """, (baekjoon_username,))
    
    deleted_count = cursor.rowcount
    print(f"Se eliminaron {deleted_count} problemas del ladder")
    
    # 4. Agregar el problema 21065 como 'current'
    print(f"Agregando problema {problem_id} como 'current'...")
    
    cursor.execute("""
    INSERT INTO ladder_problems 
    (baekjoon_username, position, problem_id, problem_title, state) 
    VALUES (%s, %s, %s, %s, %s)
    """, (baekjoon_username, 1, problem_id, problem_title, 'current'))
    
    # 5. Confirmar cambios y verificar
    conn.commit()
    print("Cambios guardados en la base de datos")
    
    # 6. Verificar que el problema está correctamente configurado
    cursor.execute("""
    SELECT id, position, problem_id, problem_title, state
    FROM ladder_problems
    WHERE baekjoon_username = %s
    ORDER BY position
    """, (baekjoon_username,))
    
    ladder_problems = cursor.fetchall()
    
    print("\n=== LADDER ACTUALIZADO ===")
    if ladder_problems:
        print(f"{'ID':<5} | {'Pos':<4} | {'Problem ID':<10} | {'State':<8} | {'Title'}")
        print("-" * 80)
        for problem in ladder_problems:
            print(f"{problem[0]:<5} | {problem[1]:<4} | {problem[2]:<10} | {problem[4]:<8} | {problem[3]}")
    else:
        print("ERROR: No se encontraron problemas en el ladder después de la reparación")
    
    # Cerrar conexión
    cursor.close()
    conn.close()
    
    print("\n=== LADDER REPARADO EXITOSAMENTE ===")
    print(f"Ahora el problema {problem_id} ({problem_title}) está configurado como 'current'")
    print("Por favor visita /account/1/ladder para verificar que todo funcione correctamente")
    print("Usa el botón 'Verificar' en la interfaz para verificar el problema")
    
except Exception as e:
    print(f"ERROR: {str(e)}")
    try:
        conn.rollback()
    except:
        pass
    sys.exit(1) 