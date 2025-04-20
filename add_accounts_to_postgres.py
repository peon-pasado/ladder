import psycopg2
from datetime import datetime

# Cuentas a agregar
ACCOUNTS_TO_ADD = [
    {'username': 'hhs2003', 'user_id': 1},  # Agregar a user_id 1 (admin)
    {'username': 'cegax', 'user_id': 1}     # Agregar a user_id 1 (admin)
]

# Conexión a PostgreSQL
pg_url = "postgresql://ladder_db_user:6FCOPInpMsKIazgN7WbdXd1dzsUwZVmv@dpg-d01m3rruibrs73aurmt0-a.virginia-postgres.render.com/ladder_db"

print("AGREGANDO CUENTAS A POSTGRESQL")
print("=============================")

try:
    # Conectar a PostgreSQL
    conn = psycopg2.connect(pg_url)
    cursor = conn.cursor()
    
    # Verificar cuentas existentes
    cursor.execute("SELECT baekjoon_username FROM baekjoon_accounts")
    existing_accounts = [row[0] for row in cursor.fetchall()]
    print(f"Cuentas existentes: {existing_accounts}")
    
    # Agregar cada cuenta
    for account in ACCOUNTS_TO_ADD:
        username = account['username']
        user_id = account['user_id']
        
        if username not in existing_accounts:
            print(f"Agregando cuenta: {username} (user_id: {user_id})")
            
            # Insertar la cuenta
            cursor.execute(
                """
                INSERT INTO baekjoon_accounts 
                (user_id, baekjoon_username, added_on) 
                VALUES (%s, %s, %s)
                RETURNING id
                """,
                (user_id, username, datetime.now())
            )
            
            new_id = cursor.fetchone()[0]
            conn.commit()
            
            print(f"✅ Cuenta agregada exitosamente con ID: {new_id}")
        else:
            print(f"La cuenta {username} ya existe en la base de datos")
    
    # Verificar el resultado final
    cursor.execute("SELECT id, user_id, baekjoon_username FROM baekjoon_accounts ORDER BY id")
    all_accounts = cursor.fetchall()
    
    print("\nCuentas en PostgreSQL después de la actualización:")
    for account in all_accounts:
        print(f"  - ID: {account[0]}, User ID: {account[1]}, Username: {account[2]}")
    
    # Cerrar conexión
    cursor.close()
    conn.close()
    
    print("\n✨ Proceso completado exitosamente")
    print("Ahora puedes acceder al ladder de estas cuentas desde la interfaz web.")
    print("El sistema inicializará automáticamente el ladder con problemas recomendados.")
    
except Exception as e:
    print(f"ERROR: {str(e)}")
    try:
        conn.rollback()
        conn.close()
    except:
        pass 