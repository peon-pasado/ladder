import psycopg2
import sys

# Conexión a la base de datos
DATABASE_URL = "postgresql://ladder_db_user:6FCOPInpMsKIazgN7WbdXd1dzsUwZVmv@dpg-d01m3rruibrs73aurmt0-a.virginia-postgres.render.com/ladder_db"

# Cuenta a buscar
SEARCH_TERM = "hhs2003"

try:
    # Conectar a la base de datos
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    print(f"BÚSQUEDA EXHAUSTIVA PARA LA CUENTA '{SEARCH_TERM}'")
    print("=" * 60)
    
    # 1. Buscar en baekjoon_accounts (búsqueda exacta)
    cursor.execute("SELECT id, user_id, baekjoon_username FROM baekjoon_accounts WHERE baekjoon_username = %s", (SEARCH_TERM,))
    exact_match = cursor.fetchall()
    
    if exact_match:
        print(f"✅ COINCIDENCIA EXACTA encontrada:")
        for account in exact_match:
            print(f"  ID: {account[0]}, User ID: {account[1]}, Username: {account[2]}")
    else:
        print(f"❌ No se encontró coincidencia exacta para '{SEARCH_TERM}'")
    
    # 2. Buscar coincidencias parciales (LIKE)
    cursor.execute("SELECT id, user_id, baekjoon_username FROM baekjoon_accounts WHERE baekjoon_username LIKE %s", (f"%{SEARCH_TERM}%",))
    partial_matches = cursor.fetchall()
    
    if partial_matches:
        print(f"\n✅ COINCIDENCIAS PARCIALES encontradas:")
        for account in partial_matches:
            print(f"  ID: {account[0]}, User ID: {account[1]}, Username: {account[2]}")
    else:
        print(f"\n❌ No se encontraron coincidencias parciales para '{SEARCH_TERM}'")
    
    # 3. Buscar cualquier coincidencia con "hhs" o "2003"
    cursor.execute("""
    SELECT id, user_id, baekjoon_username 
    FROM baekjoon_accounts 
    WHERE baekjoon_username LIKE %s OR baekjoon_username LIKE %s
    """, (f"%hhs%", f"%2003%"))
    
    pattern_matches = cursor.fetchall()
    
    if pattern_matches:
        print(f"\n✅ COINCIDENCIAS POR PATRÓN ('hhs' o '2003'):")
        for account in pattern_matches:
            print(f"  ID: {account[0]}, User ID: {account[1]}, Username: {account[2]}")
    else:
        print(f"\n❌ No se encontraron coincidencias con los patrones 'hhs' o '2003'")
    
    # 4. Comprobar si hay alguna cuenta asociada con problemas en ladder_problems
    print("\nBuscando en ladder_problems...")
    cursor.execute("SELECT DISTINCT baekjoon_username FROM ladder_problems")
    ladder_usernames = cursor.fetchall()
    
    print(f"Usuarios en ladder_problems ({len(ladder_usernames)}):")
    for username in ladder_usernames:
        print(f"  - {username[0]}")
        
        # Comprobar si tiene alguna similitud con hhs2003
        if "hhs" in username[0].lower() or "2003" in username[0]:
            print(f"    ⚠️ POSIBLE COINCIDENCIA con '{SEARCH_TERM}'")
    
    # 5. Comprobar si hay alguna incidencia de la cadena en toda la base de datos (tablas principales)
    print("\nBuscando menciones en otras tablas principales...")
    
    # 5.1 Tabla users
    cursor.execute("SELECT id, username FROM users WHERE username LIKE %s", (f"%{SEARCH_TERM}%",))
    user_matches = cursor.fetchall()
    
    if user_matches:
        print(f"Encontrado en tabla 'users':")
        for user in user_matches:
            print(f"  ID: {user[0]}, Username: {user[1]}")
    
    # 5.2 Tabla solved_problems (si existe)
    try:
        cursor.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'solved_problems'")
        if cursor.fetchone()[0] > 0:
            cursor.execute("""
            SELECT sp.id, sp.user_id, u.username
            FROM solved_problems sp
            JOIN users u ON sp.user_id = u.id
            WHERE sp.problem_title LIKE %s
            LIMIT 5
            """, (f"%{SEARCH_TERM}%",))
            
            solved_matches = cursor.fetchall()
            
            if solved_matches:
                print(f"Encontrado en tabla 'solved_problems':")
                for solved in solved_matches:
                    print(f"  ID: {solved[0]}, User ID: {solved[1]}, Username: {solved[2]}")
    except:
        print("No se pudo buscar en la tabla solved_problems")
    
    # 6. Mostrar todas las cuentas baekjoon
    print("\n=== TODAS LAS CUENTAS BAEKJOON ===")
    cursor.execute("SELECT id, user_id, baekjoon_username FROM baekjoon_accounts ORDER BY id")
    all_accounts = cursor.fetchall()
    
    print(f"Total: {len(all_accounts)} cuentas")
    for account in all_accounts:
        print(f"  ID: {account[0]}, User ID: {account[1]}, Username: {account[2]}")
        
        # Obtener el username del usuario vinculado
        cursor.execute("SELECT username FROM users WHERE id = %s", (account[1],))
        username = cursor.fetchone()
        if username:
            print(f"    👤 Usuario vinculado: {username[0]}")
    
    # 7. Obtener información sobre la URL de la base de datos
    print("\n=== INFORMACIÓN DE LA BASE DE DATOS ===")
    cursor.execute("SELECT current_database(), current_user")
    db_info = cursor.fetchone()
    
    print(f"Base de datos: {db_info[0]}")
    print(f"Usuario: {db_info[1]}")
    
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