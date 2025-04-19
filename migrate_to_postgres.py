import os
import sqlite3
import psycopg2
import sys
from psycopg2.extras import RealDictCursor

def migrate_to_postgres():
    """
    Migra los datos desde la base de datos SQLite a PostgreSQL.
    
    Antes de ejecutar este script, asegúrate de:
    1. Tener una base de datos PostgreSQL configurada
    2. Establecer la variable de entorno DATABASE_URL con la cadena de conexión a PostgreSQL
    3. Que la base de datos SQLite exista y tenga datos
    """
    
    # Verificar que existe la variable DATABASE_URL
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("Error: No se ha definido la variable de entorno DATABASE_URL")
        print("Ejemplo: postgresql://usuario:contraseña@hostname:5432/nombre_db")
        sys.exit(1)
    
    # Ruta de la base de datos SQLite
    sqlite_db_path = 'app.db'
    
    if not os.path.exists(sqlite_db_path):
        print(f"Error: No se encuentra la base de datos SQLite en {sqlite_db_path}")
        sys.exit(1)
    
    print("Iniciando migración de SQLite a PostgreSQL...")
    
    try:
        # Conexión a SQLite
        sqlite_conn = sqlite3.connect(sqlite_db_path)
        sqlite_conn.row_factory = sqlite3.Row
        sqlite_cursor = sqlite_conn.cursor()
        
        # Conexión a PostgreSQL
        pg_conn = psycopg2.connect(database_url)
        pg_cursor = pg_conn.cursor()
        
        # 1. Migrar tabla de usuarios
        print("Migrando tabla de usuarios...")
        sqlite_cursor.execute("SELECT * FROM users")
        users = sqlite_cursor.fetchall()
        
        for user in users:
            # Verificar si el usuario ya existe en PostgreSQL
            pg_cursor.execute("SELECT id FROM users WHERE username = %s", (user['username'],))
            existing_user = pg_cursor.fetchone()
            
            if not existing_user:
                pg_cursor.execute(
                    "INSERT INTO users (username, email, password_hash, rating) VALUES (%s, %s, %s, %s)",
                    (user['username'], user['email'], user['password_hash'], user['rating'])
                )
        
        pg_conn.commit()
        print(f"Migrados {len(users)} usuarios")
        
        # 2. Migrar tabla de cuentas Baekjoon
        print("Migrando cuentas de Baekjoon...")
        sqlite_cursor.execute("SELECT * FROM baekjoon_accounts")
        accounts = sqlite_cursor.fetchall()
        
        for account in accounts:
            # Buscar el ID de usuario en PostgreSQL
            pg_cursor.execute("SELECT id FROM users WHERE id = %s", (account['user_id'],))
            user_exists = pg_cursor.fetchone()
            
            if user_exists:
                try:
                    pg_cursor.execute(
                        "INSERT INTO baekjoon_accounts (user_id, baekjoon_username, added_on) VALUES (%s, %s, %s)",
                        (account['user_id'], account['baekjoon_username'], account['added_on'])
                    )
                except psycopg2.errors.UniqueViolation:
                    # Si ya existe, ignorar
                    pg_conn.rollback()
                    continue
                
                pg_conn.commit()
        
        print(f"Migradas {len(accounts)} cuentas de Baekjoon")
        
        # 3. Migrar tabla de problemas del ladder
        print("Migrando problemas del ladder...")
        sqlite_cursor.execute("SELECT * FROM ladder_problems")
        problems = sqlite_cursor.fetchall()
        
        problem_count = 0
        for problem in problems:
            try:
                pg_cursor.execute(
                    """
                    INSERT INTO ladder_problems 
                    (baekjoon_username, position, problem_id, problem_title, state) 
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (
                        problem['baekjoon_username'], 
                        problem['position'], 
                        problem['problem_id'], 
                        problem['problem_title'], 
                        problem['state']
                    )
                )
                problem_count += 1
                pg_conn.commit()
            except psycopg2.errors.UniqueViolation:
                # Si ya existe, ignorar
                pg_conn.rollback()
                continue
        
        print(f"Migrados {problem_count} problemas del ladder")
        
        # 4. Migrar tabla de problemas resueltos
        print("Migrando problemas resueltos...")
        sqlite_cursor.execute("SELECT * FROM solved_problems")
        solved = sqlite_cursor.fetchall()
        
        solved_count = 0
        for problem in solved:
            # Verificar que el usuario existe
            pg_cursor.execute("SELECT id FROM users WHERE id = %s", (problem['user_id'],))
            user_exists = pg_cursor.fetchone()
            
            if user_exists:
                try:
                    pg_cursor.execute(
                        """
                        INSERT INTO solved_problems 
                        (user_id, problem_id, problem_title, position, solved_at) 
                        VALUES (%s, %s, %s, %s, %s)
                        """,
                        (
                            problem['user_id'], 
                            problem['problem_id'], 
                            problem['problem_title'], 
                            problem['position'], 
                            problem['solved_at']
                        )
                    )
                    solved_count += 1
                    pg_conn.commit()
                except psycopg2.errors.UniqueViolation:
                    # Si ya existe, ignorar
                    pg_conn.rollback()
                    continue
        
        print(f"Migrados {solved_count} problemas resueltos")
        
        # 5. Migrar whitelist de correos
        print("Migrando whitelist de correos...")
        sqlite_cursor.execute("SELECT * FROM email_whitelist")
        whitelist = sqlite_cursor.fetchall()
        
        whitelist_count = 0
        for email in whitelist:
            try:
                pg_cursor.execute(
                    "INSERT INTO email_whitelist (email, added_at, notes) VALUES (%s, %s, %s)",
                    (email['email'], email['added_at'], email['notes'])
                )
                whitelist_count += 1
                pg_conn.commit()
            except psycopg2.errors.UniqueViolation:
                # Si ya existe, ignorar
                pg_conn.rollback()
                continue
        
        print(f"Migrados {whitelist_count} correos de la whitelist")
        
        # Cerrar conexiones
        sqlite_conn.close()
        pg_conn.close()
        
        print("\nMigración completada con éxito!")
        print("Ahora puedes ejecutar la aplicación con la variable DATABASE_URL configurada")
        print("para usar la base de datos PostgreSQL.")
        
    except Exception as e:
        print(f"Error durante la migración: {e}")
        sys.exit(1)

if __name__ == '__main__':
    migrate_to_postgres() 