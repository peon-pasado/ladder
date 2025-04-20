import psycopg2
import os
import sys

# Obtener la URL de conexión de la variable de entorno
DATABASE_URL = os.environ.get('DATABASE_URL')
if not DATABASE_URL:
    DATABASE_URL = "postgresql://ladder_db_user:6FCOPInpMsKIazgN7WbdXd1dzsUwZVmv@dpg-d01m3rruibrs73aurmt0-a.virginia-postgres.render.com/ladder_db"

print(f"Conectando a PostgreSQL con URL: {DATABASE_URL}")

try:
    # Conectar a la base de datos
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    # Problema específico a verificar
    problem_id = '21065'  # Este es el problema que el usuario mencionó
    user_id = 1  # ID del usuario admin
    
    # 1. Verificar datos de usuario
    cursor.execute("SELECT username FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    if not user:
        print(f"ERROR: Usuario con ID {user_id} no encontrado")
        sys.exit(1)
    username = user[0]
    print(f"Verificando para usuario: {username} (ID: {user_id})")
    
    # 2. Verificar cuenta Baekjoon asociada
    cursor.execute("SELECT baekjoon_username FROM baekjoon_accounts WHERE user_id = %s", (user_id,))
    account = cursor.fetchone()
    if not account:
        print(f"ERROR: Usuario no tiene cuenta Baekjoon asociada")
        sys.exit(1)
    baekjoon_username = account[0]
    print(f"Cuenta Baekjoon: {baekjoon_username}")
    
    # 3. Verificar si el problema existe en la tabla problems
    cursor.execute("SELECT problem_id, problem_title FROM problems WHERE problem_id = %s", (problem_id,))
    problem_info = cursor.fetchone()
    if problem_info:
        print(f"Problema {problem_id} encontrado en la tabla 'problems': {problem_info[1]}")
    else:
        print(f"ADVERTENCIA: Problema {problem_id} NO encontrado en la tabla 'problems'")
    
    # 4. Verificar si el problema está asignado al ladder del usuario
    cursor.execute("""
    SELECT id, position, state
    FROM ladder_problems
    WHERE baekjoon_username = %s AND problem_id = %s
    """, (baekjoon_username, problem_id))
    
    ladder_problem = cursor.fetchone()
    if ladder_problem:
        print(f"Problema {problem_id} asignado al ladder del usuario.")
        print(f"  - ID: {ladder_problem[0]}")
        print(f"  - Posición: {ladder_problem[1]}")
        print(f"  - Estado: {ladder_problem[2]}")
    else:
        print(f"ADVERTENCIA: Problema {problem_id} NO está asignado al ladder del usuario.")
        
        # Verificar si hay otros problemas en el ladder
        cursor.execute("""
        SELECT COUNT(*), MIN(problem_id), MAX(problem_id)
        FROM ladder_problems
        WHERE baekjoon_username = %s
        """, (baekjoon_username,))
        
        ladder_stats = cursor.fetchone()
        if ladder_stats and ladder_stats[0] > 0:
            print(f"  - El ladder contiene {ladder_stats[0]} problemas.")
            print(f"  - Rango de IDs: {ladder_stats[1]} a {ladder_stats[2]}")
    
    # 5. Verificar ruta de verificación en la aplicación
    # Esto es solo informativo, no puede verificarse con SQL
    print("\n=== ANÁLISIS DE LA RUTA DE VERIFICACIÓN ===")
    print(f"Ruta esperada para verificación: POST /account/{user_id}/ladder/problem/{problem_id}/verify")
    print("Nota: Esta ruta debe aceptar solicitudes POST, no GET/HEAD")
    
    # 6. Analizar lógica de verificación
    print("\n=== LÓGICA DE VERIFICACIÓN ===")
    print("Al verificar un problema, el sistema debería:")
    print("1. Comprobar que el problema existe en la tabla 'problems'")
    print("2. Comprobar que el problema está asignado al ladder del usuario")
    print("3. Verificar que el problema está en estado 'current'")
    print("4. Si todo es correcto, marcar el problema como completado y revelar el siguiente")
    
    # Verificar problema actual en el ladder
    cursor.execute("""
    SELECT problem_id, position
    FROM ladder_problems
    WHERE baekjoon_username = %s AND state = 'current'
    """, (baekjoon_username,))
    
    current_problem = cursor.fetchone()
    if current_problem:
        print(f"\nProblema actual en el ladder: {current_problem[0]} (posición {current_problem[1]})")
        
        if current_problem[0] == problem_id:
            print("✓ El problema que intentas verificar ES el problema actual. Debería funcionar.")
        else:
            print(f"✗ ERROR: El problema que intentas verificar ({problem_id}) NO es el problema actual ({current_problem[0]})")
            print("  Esto explica por qué la verificación no funciona.")
    else:
        print("✗ ERROR: No hay ningún problema marcado como 'current' en el ladder.")
    
    # 7. Verificar si hay problemas completados
    cursor.execute("""
    SELECT COUNT(*)
    FROM ladder_problems
    WHERE baekjoon_username = %s AND state = 'completed'
    """, (baekjoon_username,))
    
    completed_count = cursor.fetchone()[0]
    print(f"\nProblemas completados en el ladder: {completed_count}")
    
    # Cerrar conexión
    cursor.close()
    conn.close()
    
    print("\n=== DIAGNÓSTICO DE VERIFICACIÓN COMPLETADO ===")
    print("RECOMENDACIÓN:")
    if ladder_problem and ladder_problem[2] != 'current':
        print(f"El problema {problem_id} está en el ladder pero su estado es '{ladder_problem[2]}', no 'current'.")
        print("Para resolver esto, reinicia tu ladder y asegúrate de que este problema sea el actual.")
    elif not ladder_problem:
        print(f"El problema {problem_id} no está en tu ladder. Debes agregarlo primero.")
        
        # Sugerir cómo agregar el problema
        print("\nPara agregar este problema a tu ladder:")
        print("1. Ve a /admin/gestionar_problemas")
        print("2. Asegúrate de que el problema 21065 esté en la tabla problems")
        print("3. Usa la función 'Reiniciar Ladder' y luego intenta nuevamente")
    
except Exception as e:
    print(f"ERROR: {str(e)}")
    sys.exit(1) 