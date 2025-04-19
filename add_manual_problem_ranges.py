import sqlite3
import time
from app.utils.solved_ac_api import SolvedAcAPI
from app.utils.problem_validator import validate_problem, get_problem_info

def add_manual_problem_ranges():
    """
    Agrega los rangos específicos de problemas a la base de datos.
    Corrige el rango erróneo (20329-21058) por los rangos correctos.
    Solo agrega problemas que existan en Baekjoon.
    """
    # Rangos de problemas corregidos
    problem_ranges = [
        (20329, 20329),  # Solo el problema 20329
        (21048, 21048),  # Solo el problema 21048
        (20339, 20339),  # Solo el problema 20339
        (21050, 21058)   # Rango del 21050 al 21058
    ]
    
    # Conectar a la base de datos
    conn = sqlite3.connect('app.db')
    cursor = conn.cursor()
    
    # Crear un conjunto para evitar duplicados
    problem_ids = set()
    
    # Procesar cada rango
    for i, (start, end) in enumerate(problem_ranges, 1):
        print(f"Procesando rango {i}: {start} a {end} ({end - start + 1} problemas)")
        for problem_id in range(start, end + 1):
            problem_ids.add(str(problem_id))
    
    # Convertir el conjunto a una lista
    problem_id_list = list(problem_ids)
    
    print(f"Se procesarán {len(problem_id_list)} problemas únicos")
    
    # Asegurarse de que la tabla 'problems' existe con todos los campos necesarios
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS problems (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        problem_id TEXT UNIQUE NOT NULL,
        problem_title TEXT NOT NULL,
        tier INTEGER DEFAULT NULL,
        tags TEXT DEFAULT NULL,
        solved_count INTEGER DEFAULT 0,
        level INTEGER DEFAULT NULL,
        accepted_user_count INTEGER DEFAULT 0,
        average_tries REAL DEFAULT 0.0
    )
    ''')
    
    # Obtener los problemas que ya existen en la base de datos
    cursor.execute("SELECT problem_id FROM problems")
    existing_problems = {row[0] for row in cursor.fetchall()}
    
    # Filtrar solo los problemas que no existen en la base de datos
    new_problem_ids = [pid for pid in problem_id_list if pid not in existing_problems]
    
    if new_problem_ids:
        print(f"Validando y agregando {len(new_problem_ids)} problemas nuevos...")
        
        valid_problems = 0
        invalid_problems = 0
        
        # Procesar cada problema por separado
        for problem_id in new_problem_ids:
            print(f"Validando problema {problem_id}...", end=" ")
            
            # Verificar si el problema existe en Baekjoon
            problem_info = get_problem_info(problem_id)
            
            if problem_info:
                # El problema existe y tiene información válida
                try:
                    cursor.execute(
                        """
                        INSERT INTO problems 
                        (problem_id, problem_title, tier, tags, solved_count, level, 
                         accepted_user_count, average_tries) 
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            problem_info["problem_id"],
                            problem_info["title"],
                            problem_info["tier"],
                            problem_info["tags"],
                            problem_info["solved_count"],
                            problem_info["level"],
                            problem_info["accepted_user_count"],
                            problem_info["average_tries"]
                        )
                    )
                    print(f"VÁLIDO - Agregado: {problem_info['title']}")
                    valid_problems += 1
                except sqlite3.IntegrityError:
                    print(f"Ya existe en la base de datos")
            else:
                # El problema no existe o no tiene información suficiente
                print("INVÁLIDO - No existe en Baekjoon o no tiene información suficiente")
                invalid_problems += 1
            
            # Esperar un poco para no sobrecargar la API
            time.sleep(0.5)
            
        # Guardar los cambios
        conn.commit()
        
        # Mostrar resumen
        print(f"\nResumen:")
        print(f"- Problemas válidos agregados: {valid_problems}")
        print(f"- Problemas inválidos (no agregados): {invalid_problems}")
    
    # Contar cuántos problemas se insertaron
    cursor.execute("SELECT COUNT(*) FROM problems")
    total_problems = cursor.fetchone()[0]
    
    # Mostar información detallada
    print(f"Total de problemas en la base de datos: {total_problems}")
    
    # Verificar los problemas insertados para cada rango
    print("\nVerificación por rangos:")
    for i, (start, end) in enumerate(problem_ranges, 1):
        cursor.execute(
            """
            SELECT COUNT(*) FROM problems 
            WHERE CAST(problem_id AS INTEGER) BETWEEN ? AND ?
            """,
            (start, end)
        )
        count = cursor.fetchone()[0]
        print(f"Rango {i} ({start}-{end}): {count} problemas (esperados: {end-start+1})")
    
    conn.close()

def add_problem_range_to_user_ladder(user_id, tier_min, tier_max, count=10):
    """
    Añade problemas de un rango de tiers específico al ladder de un usuario.
    Solo se utilizarán problemas válidos de la base de datos.
    
    Args:
        user_id: ID del usuario
        tier_min: Tier mínimo
        tier_max: Tier máximo
        count: Cantidad de problemas a añadir
    """
    conn = sqlite3.connect('app.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Obtener el nombre de usuario de Baekjoon del usuario
    cursor.execute(
        """
        SELECT baekjoon_username 
        FROM baekjoon_accounts 
        WHERE user_id = ? 
        LIMIT 1
        """, 
        (user_id,)
    )
    result = cursor.fetchone()
    
    if not result:
        print(f"No se encontró una cuenta de Baekjoon para el usuario {user_id}")
        conn.close()
        return False
    
    baekjoon_username = result['baekjoon_username']
    
    # Obtener la posición más alta en el ladder actual
    cursor.execute(
        """
        SELECT MAX(position) as max_pos
        FROM ladder_problems
        WHERE baekjoon_username = ?
        """, 
        (baekjoon_username,)
    )
    result = cursor.fetchone()
    start_position = (result['max_pos'] or 0) + 1
    
    # Obtener problemas de la base de datos con el tier especificado
    # que no estén ya en el ladder del usuario
    cursor.execute(
        """
        SELECT p.* 
        FROM problems p
        LEFT JOIN ladder_problems lp ON p.problem_id = lp.problem_id AND lp.baekjoon_username = ?
        WHERE p.tier BETWEEN ? AND ?
        AND lp.id IS NULL
        AND p.tier IS NOT NULL  -- Asegurarse de que el problema tiene tier asignado
        ORDER BY p.tier ASC, p.solved_count DESC
        LIMIT ?
        """,
        (baekjoon_username, tier_min, tier_max, count)
    )
    
    problems = cursor.fetchall()
    
    if not problems:
        print(f"No se encontraron problemas disponibles en el rango de tier {tier_min}-{tier_max}")
        conn.close()
        return False
    
    print(f"Añadiendo {len(problems)} problemas al ladder de {baekjoon_username}")
    
    # Añadir los problemas al ladder
    for i, problem in enumerate(problems):
        position = start_position + i
        problem_id = problem['problem_id']
        problem_title = problem['problem_title']
        
        # Estado: el primer problema es 'current', el resto 'hidden'
        state = 'current' if position == start_position else 'hidden'
        
        cursor.execute(
            """
            INSERT INTO ladder_problems 
            (baekjoon_username, position, problem_id, problem_title, state) 
            VALUES (?, ?, ?, ?, ?)
            """,
            (baekjoon_username, position, problem_id, problem_title, state)
        )
    
    conn.commit()
    
    print(f"Se añadieron {len(problems)} problemas al ladder de {baekjoon_username}")
    
    conn.close()
    return True

if __name__ == "__main__":
    add_manual_problem_ranges()
    
    # Ejemplo de cómo añadir problemas a un ladder de usuario
    # (Esto debe ser llamado desde la interfaz de usuario normalmente)
    # add_problem_range_to_user_ladder(user_id=1, tier_min=1, tier_max=5, count=10) 