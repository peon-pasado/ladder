import psycopg2
import os
import sys
import requests

# URL de la base de datos
print("Este script no puede conectarse directamente a la base de datos remota desde tu máquina local.")
print("En su lugar, te proporcionaré instrucciones sobre cómo usar la aplicación para diagnosticar el problema.\n")

print("=== DIAGNÓSTICO DE LADDER ===")
print("Problema: Al intentar verificar el problema 21065, obtienes un error 'ladder no encontrado'")
print("\nCausas probables:")
print("1. El problema 21065 no está en tu ladder o no es el 'current'")
print("2. El ladder tiene múltiples problemas (2449-2498) cuando debería tener solo unos pocos")
print("3. La aplicación está inicializando el ladder con muchos problemas en lugar de solo uno como 'current'")

print("\n=== SOLUCIÓN RECOMENDADA ===")
print("1. Accede a tu aplicación y navega a /account/1/ladder")
print("2. Haz clic en 'Reiniciar Ladder' para limpiar tu estado actual")
print("3. Verifica qué problema aparece como 'current' (debería ser solo uno)")
print("4. Si el problema 'current' no es 21065, necesitarás agregar este problema desde el panel de administrador")

print("\nPara agregar el problema 21065 a tu ladder:")
print("1. Ve a /admin/gestionar_problemas")
print("2. Agrega el problema 21065 individualmente")
print("3. Reinicia tu ladder nuevamente y verifica que 21065 sea el problema actual")

print("\nPara verificar el problema, usa el botón 'Verificar' en la interfaz, no accedas directamente a la URL.")
print("Si necesitas diagnosticar más a fondo, considera ejecutar este script directamente en el servidor donde está desplegada la aplicación.")

print("\n=== INSTRUCCIONES ADICIONALES ===")
print("Si necesitas ejecutar este diagnóstico en el servidor, copia este script al servidor y ejecútalo con:")
print("python diagnostico_ladder.py")

print("\nPara verificar el problema actual en la aplicación, visita:")
print("https://ladder-nyqx.onrender.com/account/1/ladder")

# Obtener la URL de conexión de la variable de entorno
DATABASE_URL = os.environ.get('DATABASE_URL')
if not DATABASE_URL:
    DATABASE_URL = "postgresql://ladder_db_user:6FCOPInpMsKIazgN7WbdXd1dzsUwZVmv@dpg-d01m3rruibrs73aurmt0-a.virginia-postgres.render.com/ladder_db"

print(f"Conectando a PostgreSQL con URL: {DATABASE_URL}")

try:
    # Conectar a la base de datos
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    # Verificar usuario
    user_id = 1  # ID del usuario admin
    
    # 1. Verificar si el usuario existe
    cursor.execute("SELECT id, username FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    if user:
        print(f"Usuario encontrado: ID {user[0]}, Username: {user[1]}")
    else:
        print(f"ERROR: No se encontró usuario con ID {user_id}")
        sys.exit(1)
    
    # 2. Verificar cuenta Baekjoon asociada
    cursor.execute("SELECT id, baekjoon_username FROM baekjoon_accounts WHERE user_id = %s", (user_id,))
    account = cursor.fetchone()
    if account:
        print(f"Cuenta Baekjoon encontrada: ID {account[0]}, Username: {account[1]}")
        baekjoon_username = account[1]
    else:
        print(f"AVISO: El usuario no tiene cuenta Baekjoon asociada")
        sys.exit(1)
    
    # 3. Examinar el estado actual del ladder
    cursor.execute("""
    SELECT id, position, problem_id, problem_title, state
    FROM ladder_problems
    WHERE baekjoon_username = %s
    ORDER BY position
    """, (baekjoon_username,))
    
    ladder_problems = cursor.fetchall()
    
    print(f"\n=== LADDER ACTUAL ({len(ladder_problems)} problemas) ===")
    if ladder_problems:
        print(f"{'ID':<5} | {'Pos':<4} | {'Problem ID':<10} | {'State':<8} | {'Title'}")
        print("-" * 80)
        for problem in ladder_problems:
            print(f"{problem[0]:<5} | {problem[1]:<4} | {problem[2]:<10} | {problem[4]:<8} | {problem[3]}")
    else:
        print("No hay problemas en el ladder.")
    
    # 4. Verificar si el problema 21065 existe en la tabla problems
    cursor.execute("SELECT problem_id, problem_title FROM problems WHERE problem_id = %s", ('21065',))
    problem_21065 = cursor.fetchone()
    if problem_21065:
        print(f"\nProblema 21065 encontrado en la tabla problems: {problem_21065[1]}")
    else:
        print("\nAVISO: El problema 21065 NO existe en la tabla problems.")
    
    # 5. Verificar si el problema 21065 está en el ladder
    cursor.execute("""
    SELECT id, position, state
    FROM ladder_problems
    WHERE baekjoon_username = %s AND problem_id = %s
    """, (baekjoon_username, '21065'))
    
    problem_in_ladder = cursor.fetchone()
    if problem_in_ladder:
        print(f"Problema 21065 encontrado en el ladder: posición {problem_in_ladder[1]}, estado {problem_in_ladder[2]}")
    else:
        print("AVISO: El problema 21065 NO está asignado al ladder del usuario.")
    
    # 6. Verificar configuración de init_ladder en el código
    print("\n=== CÓDIGO DE INICIALIZACIÓN ===")
    print("Nota: Revisando cuántos problemas se asignan al inicializar...")
    
    # Examinar la lógica de inicialización en la tabla ladder_problems
    cursor.execute("""
    SELECT COUNT(*), MIN(position), MAX(position), COUNT(CASE WHEN state = 'current' THEN 1 END)
    FROM ladder_problems
    WHERE baekjoon_username = %s
    """, (baekjoon_username,))
    
    ladder_stats = cursor.fetchone()
    if ladder_stats:
        print(f"Total problemas: {ladder_stats[0]}")
        print(f"Rango de posiciones: {ladder_stats[1]} - {ladder_stats[2]}")
        print(f"Problemas 'current': {ladder_stats[3]} (debe ser 1)")
    
    # 7. Verificar problemas 'current'
    cursor.execute("""
    SELECT problem_id, position, state
    FROM ladder_problems
    WHERE baekjoon_username = %s AND state = 'current'
    """, (baekjoon_username,))
    
    current_problems = cursor.fetchall()
    print(f"\nProblemas con estado 'current': {len(current_problems)}")
    for problem in current_problems:
        print(f"  - Problema {problem[0]} en posición {problem[1]}")
    
    # Cerrar conexión
    cursor.close()
    conn.close()
    
    print("\n=== DIAGNÓSTICO COMPLETADO ===")
    
except Exception as e:
    print(f"ERROR: {str(e)}")
    sys.exit(1) 