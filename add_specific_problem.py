#!/usr/bin/env python
import psycopg2
from datetime import datetime, timedelta

# URL de la base de datos
DATABASE_URL = "postgresql://ladder_db_user:6FCOPInpMsKIazgN7WbdXd1dzsUwZVmv@dpg-d01m3rruibrs73aurmt0-a.virginia-postgres.render.com/ladder_db"

problem_id = "21065"
position = 1

print(f"Agregando el problema {problem_id} como el primer problema (current) en el ladder...")
print(f"Conectando a PostgreSQL con URL: {DATABASE_URL}")

try:
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    # 1. Verificar si el problema existe
    cursor.execute("SELECT problem_id, problem_title FROM problems WHERE problem_id = %s", (problem_id,))
    problem = cursor.fetchone()
    
    if not problem:
        print(f"❌ Error: El problema {problem_id} no existe en la base de datos")
        conn.close()
        exit(1)
    
    problem_title = problem[1]
    print(f"✅ Problema encontrado: {problem_id} - {problem_title}")
    
    # 2. Obtener todas las cuentas de Baekjoon
    cursor.execute("SELECT ba.user_id, ba.baekjoon_username, u.username FROM baekjoon_accounts ba JOIN users u ON ba.user_id = u.id")
    accounts = cursor.fetchall()
    
    if not accounts:
        print("❌ No se encontraron cuentas de Baekjoon registradas")
        conn.close()
        exit(1)
    
    # Mostrar las cuentas disponibles y pedir al usuario que elija
    print("\nCuentas disponibles:")
    for i, account in enumerate(accounts, 1):
        print(f"{i}. Usuario: {account[2]}, Baekjoon: {account[1]}")
    
    if len(accounts) == 1:
        selected = 1
        print(f"Seleccionando automáticamente la única cuenta disponible: {accounts[0][1]}")
    else:
        selected = int(input("\nSeleccione el número de la cuenta para la que quiere agregar el problema: "))
        if selected < 1 or selected > len(accounts):
            print("❌ Selección inválida")
            conn.close()
            exit(1)
    
    user_id = accounts[selected-1][0]
    baekjoon_username = accounts[selected-1][1]
    username = accounts[selected-1][2]
    
    print(f"\nAgregando problema para usuario {username} (Baekjoon: {baekjoon_username})")
    
    # 3. Desmarcar cualquier problema actual
    cursor.execute("""
    UPDATE ladder_problems 
    SET state = 'hidden' 
    WHERE baekjoon_username = %s AND state = 'current'
    """, (baekjoon_username,))
    
    unmarked = cursor.rowcount
    if unmarked > 0:
        print(f"✅ {unmarked} problemas desmarcados como current")
    
    # 4. Verificar si el problema ya existe en el ladder
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
        """, (position, datetime.now() + timedelta(hours=6), existing[0]))
        
        print(f"✅ Problema {problem_id} actualizado a estado 'current', posición {position}")
    else:
        # Si no existe, insertarlo
        cursor.execute("""
        INSERT INTO ladder_problems 
        (baekjoon_username, position, problem_id, problem_title, state, revealed_at)
        VALUES (%s, %s, %s, %s, 'current', %s)
        """, (baekjoon_username, position, problem_id, problem_title, datetime.now() + timedelta(hours=6)))
        
        print(f"✅ Problema {problem_id} agregado como 'current' en posición {position}")
    
    # 5. Verificar el estado del ladder
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
    
    print("\n✨ ¡Problema agregado con éxito!")
    
except Exception as e:
    print(f"ERROR: {str(e)}")
    try:
        conn.rollback()
        conn.close()
    except:
        pass 