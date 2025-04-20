#!/usr/bin/env python
import psycopg2
from datetime import datetime

# URL de la base de datos
DATABASE_URL = "postgresql://ladder_db_user:6FCOPInpMsKIazgN7WbdXd1dzsUwZVmv@dpg-d01m3rruibrs73aurmt0-a.virginia-postgres.render.com/ladder_db"

print("CORRECCIÓN COMPLETA DE CUENTAS Y LADDER")
print(f"Conectando a PostgreSQL con URL: {DATABASE_URL}")

try:
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    # 1. Mostrar el estado actual de las tablas
    print("\n1. ESTADO ACTUAL DE LAS TABLAS:")
    
    # Usuarios
    cursor.execute("SELECT id, username FROM users")
    users = cursor.fetchall()
    print("\nUsuarios:")
    for user in users:
        print(f"ID: {user[0]}, Username: {user[1]}")
    
    # Cuentas de Baekjoon
    cursor.execute("SELECT user_id, baekjoon_username FROM baekjoon_accounts")
    accounts = cursor.fetchall()
    print("\nCuentas de Baekjoon:")
    for account in accounts:
        print(f"User ID: {account[0]}, Baekjoon Username: {account[1]}")
    
    # Problemas en ladder
    cursor.execute("SELECT id, baekjoon_username, problem_id, state, position, problem_title FROM ladder_problems")
    problems = cursor.fetchall()
    print("\nProblemas en ladder:")
    for problem in problems:
        print(f"ID: {problem[0]}, Baekjoon: {problem[1]}, Problem ID: {problem[2]}, State: {problem[3]}, Position: {problem[4]}, Title: {problem[5]}")
    
    # 2. Corregir cuentas de Baekjoon
    print("\n2. CORRIGIENDO CUENTAS DE BAEKJOON:")
    
    # Borrar todas las cuentas existentes
    cursor.execute("DELETE FROM baekjoon_accounts")
    deleted_accounts = cursor.rowcount
    print(f"Se eliminaron {deleted_accounts} cuentas de Baekjoon")
    
    # Crear cuenta para admin (user_id 1) con username "fischer"
    cursor.execute("INSERT INTO baekjoon_accounts (user_id, baekjoon_username) VALUES (1, 'fischer')")
    print("✅ Creada cuenta de Baekjoon 'fischer' para usuario admin (ID: 1)")
    
    # Crear cuentas para los demás usuarios con su ID como nombre
    for user in users:
        if user[0] != 1:  # Omitir admin que ya tiene cuenta
            cursor.execute("INSERT INTO baekjoon_accounts (user_id, baekjoon_username) VALUES (%s, %s)", 
                         (user[0], str(user[0])))
            print(f"✅ Creada cuenta de Baekjoon '{user[0]}' para usuario {user[1]} (ID: {user[0]})")
    
    # 3. Limpiar y reiniciar el ladder para fischer
    print("\n3. REINICIANDO LADDER PARA FISCHER:")
    
    # Eliminar todos los problemas actuales para todas las cuentas
    cursor.execute("DELETE FROM ladder_problems")
    deleted_problems = cursor.rowcount
    print(f"Se eliminaron {deleted_problems} problemas de todos los ladders")
    
    # Obtener el problema 21065
    cursor.execute("SELECT problem_id, problem_title FROM problems WHERE problem_id = '21065'")
    problem_21065 = cursor.fetchone()
    
    if problem_21065:
        # Insertar el problema 21065 como current para fischer
        cursor.execute("""
        INSERT INTO ladder_problems 
        (baekjoon_username, position, problem_id, problem_title, state, revealed_at)
        VALUES ('fischer', 1, %s, %s, 'current', %s)
        """, (problem_21065[0], problem_21065[1], datetime.now()))
        
        print(f"✅ Agregado problema {problem_21065[0]} ({problem_21065[1]}) como current para fischer")
    else:
        print("❌ No se encontró el problema 21065 en la base de datos")
    
    # 4. Verificar el estado final de las tablas
    print("\n4. ESTADO FINAL DE LAS TABLAS:")
    
    # Cuentas de Baekjoon
    cursor.execute("SELECT user_id, baekjoon_username FROM baekjoon_accounts")
    final_accounts = cursor.fetchall()
    print("\nCuentas de Baekjoon finales:")
    for account in final_accounts:
        cursor.execute("SELECT username FROM users WHERE id = %s", (account[0],))
        username = cursor.fetchone()[0]
        print(f"User ID: {account[0]} ({username}), Baekjoon Username: {account[1]}")
    
    # Problemas en ladder
    cursor.execute("SELECT id, baekjoon_username, problem_id, state, position, problem_title FROM ladder_problems")
    final_problems = cursor.fetchall()
    print("\nProblemas en ladder finales:")
    for problem in final_problems:
        print(f"ID: {problem[0]}, Baekjoon: {problem[1]}, Problem ID: {problem[2]}, State: {problem[3]}, Position: {problem[4]}, Title: {problem[5]}")
    
    # Confirmar cambios
    conn.commit()
    conn.close()
    
    print("\n✨ CORRECCIÓN COMPLETA ✨")
    print("Las cuentas de Baekjoon y los problemas en el ladder han sido corregidos.")
    print("Usuario admin (ID: 1) ahora tiene la cuenta de Baekjoon 'fischer'.")
    print("El problema 21065 ha sido asignado como el único problema en el ladder de fischer.")
    print("Por favor, reinicia la aplicación web y verifica que el problema correcto aparezca.")
    
except Exception as e:
    print(f"ERROR: {str(e)}")
    try:
        conn.rollback()
        conn.close()
    except:
        pass 