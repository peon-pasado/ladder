import sqlite3
import os

def init_db():
    db_exists = os.path.exists('app.db')
    
    # Conectar a la base de datos (la crea si no existe)
    conn = sqlite3.connect('app.db')
    cursor = conn.cursor()
    
    if not db_exists:
        print("Creando nueva base de datos...")
        # Crear tabla de usuarios
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            rating INTEGER DEFAULT 1500
        )
        ''')
        
        # Crear tabla para cuentas de Baekjoon
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS baekjoon_accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            baekjoon_username TEXT NOT NULL,
            added_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            UNIQUE(user_id, baekjoon_username)
        )
        ''')
        
        # Crear tabla para problemas del ladder
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS ladder_problems (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            baekjoon_username TEXT NOT NULL,
            position INTEGER NOT NULL,
            problem_id TEXT NOT NULL,
            problem_title TEXT NOT NULL,
            state TEXT DEFAULT 'hidden',
            UNIQUE(baekjoon_username, position)
        )
        ''')
    
    # Verificar si la tabla de problemas resueltos ya existe
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='solved_problems'")
    table_exists = cursor.fetchone()
    
    if not table_exists:
        print("Añadiendo tabla de problemas resueltos...")
        # Crear tabla para problemas resueltos con posición en leaderboard
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS solved_problems (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            problem_id TEXT NOT NULL,
            problem_title TEXT NOT NULL,
            position INTEGER NOT NULL,
            solved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            UNIQUE(user_id, problem_id)
        )
        ''')
        print("Tabla de problemas resueltos añadida correctamente")
    else:
        print("La tabla de problemas resueltos ya existe")
    
    # Verificar si la columna rating existe en la tabla users
    cursor.execute("PRAGMA table_info(users)")
    columns = cursor.fetchall()
    has_rating = any(col[1] == 'rating' for col in columns)
    
    if not has_rating:
        print("Añadiendo columna rating a la tabla users...")
        cursor.execute('''
        ALTER TABLE users ADD COLUMN rating INTEGER DEFAULT 1500
        ''')
        print("Columna rating añadida correctamente")
    
    # Si la base de datos ya existe, verificamos si necesitamos migrar la tabla ladder_problems
    if db_exists:
        print("Verificando si es necesario migrar la tabla ladder_problems...")
        # Comprobar si la estructura actual tiene account_id en lugar de baekjoon_username
        cursor.execute("PRAGMA table_info(ladder_problems)")
        columns = cursor.fetchall()
        
        has_account_id = any(col[1] == 'account_id' for col in columns)
        has_baekjoon_username = any(col[1] == 'baekjoon_username' for col in columns)
        
        if has_account_id and not has_baekjoon_username:
            print("Migrando tabla ladder_problems...")
            
            # Crear una tabla temporal con la nueva estructura
            cursor.execute('''
            CREATE TABLE ladder_problems_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                baekjoon_username TEXT NOT NULL,
                position INTEGER NOT NULL,
                problem_id TEXT NOT NULL,
                problem_title TEXT NOT NULL,
                state TEXT DEFAULT 'hidden',
                UNIQUE(baekjoon_username, position)
            )
            ''')
            
            # Migrar los datos
            cursor.execute('''
            INSERT INTO ladder_problems_new (baekjoon_username, position, problem_id, problem_title, state)
            SELECT ba.baekjoon_username, lp.position, lp.problem_id, lp.problem_title, lp.state
            FROM ladder_problems lp
            JOIN baekjoon_accounts ba ON lp.account_id = ba.id
            ''')
            
            # Eliminar la tabla antigua
            cursor.execute("DROP TABLE ladder_problems")
            
            # Renombrar la nueva tabla
            cursor.execute("ALTER TABLE ladder_problems_new RENAME TO ladder_problems")
            
            print("Migración completada correctamente")
    
    # Guardar los cambios y cerrar la conexión
    conn.commit()
    conn.close()
    
    print("Base de datos inicializada/actualizada con éxito.")

if __name__ == '__main__':
    init_db() 