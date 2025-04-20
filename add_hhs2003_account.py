import psycopg2
import sys
from datetime import datetime

# Conexión a la base de datos
DATABASE_URL = "postgresql://ladder_db_user:6FCOPInpMsKIazgN7WbdXd1dzsUwZVmv@dpg-d01m3rruibrs73aurmt0-a.virginia-postgres.render.com/ladder_db"

# Cuenta a agregar
BAEKJOON_USERNAME = "hhs2003"

# El usuario al que se asociará la cuenta (cambiar según sea necesario)
# Opciones: 1 (admin), 2 (JhoZzel), 3 (mika_uwu)
USER_ID = 1  # Por defecto, admin

def print_separator():
    print("=" * 50)

try:
    # Conectar a la base de datos
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    print_separator()
    print(f"AGREGANDO CUENTA BAEKJOON '{BAEKJOON_USERNAME}' AL USUARIO ID {USER_ID}")
    print_separator()
    
    # 1. Verificar que el usuario existe
    cursor.execute("SELECT username FROM users WHERE id = %s", (USER_ID,))
    user = cursor.fetchone()
    
    if not user:
        print(f"ERROR: El usuario con ID {USER_ID} no existe")
        sys.exit(1)
    
    print(f"Usuario encontrado: {user[0]} (ID: {USER_ID})")
    
    # 2. Verificar si la cuenta de Baekjoon ya existe
    cursor.execute("SELECT id FROM baekjoon_accounts WHERE baekjoon_username = %s", (BAEKJOON_USERNAME,))
    existing_account = cursor.fetchone()
    
    if existing_account:
        print(f"AVISO: La cuenta '{BAEKJOON_USERNAME}' ya existe en el sistema (ID: {existing_account[0]})")
        sys.exit(1)
    
    # 3. Insertar la nueva cuenta Baekjoon
    print(f"\nAgregando cuenta '{BAEKJOON_USERNAME}' para el usuario {user[0]}...")
    
    cursor.execute("""
    INSERT INTO baekjoon_accounts (user_id, baekjoon_username, created_at)
    VALUES (%s, %s, %s)
    RETURNING id
    """, (USER_ID, BAEKJOON_USERNAME, datetime.now()))
    
    new_account_id = cursor.fetchone()[0]
    conn.commit()
    
    print(f"✅ Cuenta agregada exitosamente (ID: {new_account_id})")
    
    # 4. Inicializar el ladder para esta cuenta
    print("\nInicializando ladder para la nueva cuenta...")
    
    # 4.1 Buscar un problema para asignar
    cursor.execute("SELECT problem_id, problem_title FROM problems WHERE problem_id = '21065'")
    problem = cursor.fetchone()
    
    if not problem:
        # Si no existe, buscar cualquier problema
        cursor.execute("SELECT problem_id, problem_title FROM problems ORDER BY problem_id LIMIT 1")
        problem = cursor.fetchone()
        
        if not problem:
            print("⚠️ No hay problemas disponibles en la base de datos")
            sys.exit(1)
    
    problem_id = problem[0]
    problem_title = problem[1]
    
    # 4.2 Insertar el problema en el ladder como 'current'
    cursor.execute("""
    INSERT INTO ladder_problems 
    (baekjoon_username, position, problem_id, problem_title, state, revealed_at)
    VALUES (%s, %s, %s, %s, %s, %s)
    RETURNING id
    """, (BAEKJOON_USERNAME, 1, problem_id, problem_title, 'current', datetime.now()))
    
    ladder_problem_id = cursor.fetchone()[0]
    conn.commit()
    
    print(f"✅ Ladder inicializado con el problema {problem_id} ({problem_title})")
    
    # 5. Verificar el estado final
    cursor.execute("""
    SELECT lp.id, lp.problem_id, lp.problem_title, lp.state, ba.id, ba.baekjoon_username
    FROM ladder_problems lp
    JOIN baekjoon_accounts ba ON lp.baekjoon_username = ba.baekjoon_username
    WHERE ba.baekjoon_username = %s
    """, (BAEKJOON_USERNAME,))
    
    result = cursor.fetchone()
    
    print_separator()
    print("RESULTADO FINAL:")
    print(f"Cuenta Baekjoon: {result[5]} (ID: {result[4]})")
    print(f"Problema asignado: {result[1]} - {result[2]} (ID: {result[0]}, Estado: {result[3]})")
    print_separator()
    
    print("\n✨ Proceso completado exitosamente")
    print(f"Ahora puedes acceder al ladder para la cuenta '{BAEKJOON_USERNAME}' desde la interfaz")
    
    # Cerrar conexión
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"ERROR: {str(e)}")
    try:
        conn.rollback()
        conn.close()
    except:
        pass
    sys.exit(1) 