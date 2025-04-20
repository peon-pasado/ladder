#!/usr/bin/env python
import psycopg2
from datetime import datetime, timedelta

# URL de la base de datos
DATABASE_URL = "postgresql://ladder_db_user:6FCOPInpMsKIazgN7WbdXd1dzsUwZVmv@dpg-d01m3rruibrs73aurmt0-a.virginia-postgres.render.com/ladder_db"

problem_id = "21065"
user_id = 1  # ID de admin
position = 1
correct_baekjoon_username = "fischer"  # Nombre correcto en Baekjoon

print(f"Corrigiendo la cuenta de Baekjoon para admin (ID: {user_id}) a '{correct_baekjoon_username}'...")
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
    
    # Obtener la cuenta de Baekjoon actual
    cursor.execute("SELECT baekjoon_username FROM baekjoon_accounts WHERE user_id = %s", (user_id,))
    baekjoon_account = cursor.fetchone()
    
    if not baekjoon_account:
        # Si no existe cuenta, crear una con el nombre correcto
        cursor.execute("INSERT INTO baekjoon_accounts (user_id, baekjoon_username) VALUES (%s, %s)", 
                      (user_id, correct_baekjoon_username))
        print(f"✅ Creada cuenta de Baekjoon para usuario {username}: {correct_baekjoon_username}")
    else:
        old_username = baekjoon_account[0]
        # Actualizar cualquier problema existente para el usuario de Baekjoon antiguo
        cursor.execute("""
        UPDATE ladder_problems 
        SET baekjoon_username = %s
        WHERE baekjoon_username = %s
        """, (correct_baekjoon_username, old_username))
        
        updated_problems = cursor.rowcount
        
        # Actualizar el nombre de usuario de Baekjoon
        cursor.execute("""
        UPDATE baekjoon_accounts 
        SET baekjoon_username = %s
        WHERE user_id = %s
        """, (correct_baekjoon_username, user_id))
        
        print(f"✅ Actualizada cuenta de Baekjoon de '{old_username}' a '{correct_baekjoon_username}'")
        if updated_problems > 0:
            print(f"✅ {updated_problems} problemas actualizados a la nueva cuenta")
    
    # Verificar si el problema existe
    cursor.execute("SELECT problem_id, problem_title FROM problems WHERE problem_id = %s", (problem_id,))
    problem = cursor.fetchone()
    
    if not problem:
        print(f"❌ Error: El problema {problem_id} no existe en la base de datos")
        conn.close()
        exit(1)
    
    problem_title = problem[1]
    print(f"✅ Problema encontrado: {problem_id} - {problem_title}")
    
    # Desmarcar cualquier problema actual en el ladder
    cursor.execute("""
    UPDATE ladder_problems 
    SET state = 'hidden' 
    WHERE baekjoon_username = %s AND state = 'current'
    """, (correct_baekjoon_username,))
    
    unmarked = cursor.rowcount
    if unmarked > 0:
        print(f"✅ {unmarked} problemas desmarcados como current")
    
    # Verificar si el problema ya existe en el ladder
    cursor.execute("""
    SELECT id, state FROM ladder_problems 
    WHERE baekjoon_username = %s AND problem_id = %s
    """, (correct_baekjoon_username, problem_id))
    
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
        """, (correct_baekjoon_username, position, problem_id, problem_title, datetime.now()))
        
        print(f"✅ Problema {problem_id} agregado como 'current' en posición {position}")
    
    # Verificar el estado del ladder
    cursor.execute("""
    SELECT id, position, problem_id, problem_title, state, revealed_at 
    FROM ladder_problems
    WHERE baekjoon_username = %s
    ORDER BY position
    """, (correct_baekjoon_username,))
    
    ladder = cursor.fetchall()
    
    print(f"\nLadder actualizado para {correct_baekjoon_username} (usuario {username}):")
    print(f"{'ID':<5} | {'Pos':<5} | {'Problem ID':<10} | {'Estado':<10} | {'Título'}")
    print("-" * 80)
    
    for p in ladder:
        print(f"{p[0]:<5} | {p[1]:<5} | {p[2]:<10} | {p[4]:<10} | {p[3]}")
    
    conn.commit()
    conn.close()
    
    print("\n✨ ¡Cuenta corregida y problema agregado con éxito al ladder de fischer!")
    
except Exception as e:
    print(f"ERROR: {str(e)}")
    try:
        conn.rollback()
        conn.close()
    except:
        pass 