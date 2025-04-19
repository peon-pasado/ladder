import sqlite3
import time
from app.utils.solved_ac_api import SolvedAcAPI

def fix_all_problems():
    """
    Revisa todos los problemas en el ladder y actualiza o reemplaza los que tengan
    información genérica o sean inválidos.
    """
    print("Iniciando revisión y corrección de problemas...")
    
    # Conectar a la base de datos
    conn = sqlite3.connect('app.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Obtener problemas con títulos genéricos
    cursor.execute(
        """
        SELECT lp.problem_id, lp.problem_title, lp.baekjoon_username
        FROM ladder_problems lp
        WHERE lp.problem_title LIKE 'Problema %'
        """
    )
    
    generic_problems = cursor.fetchall()
    print(f"Se encontraron {len(generic_problems)} problemas con títulos genéricos")
    
    # Procesar cada problema genérico
    problems_fixed = 0
    problems_replaced = 0
    
    for problem in generic_problems:
        problem_id = problem["problem_id"]
        baekjoon_username = problem["baekjoon_username"]
        
        print(f"\nProcesando problema {problem_id} para usuario {baekjoon_username}...")
        
        # Intentar obtener información actualizada desde Solved.ac
        problem_data = SolvedAcAPI.get_problem_by_id(problem_id)
        
        if problem_data:
            # El problema existe en Solved.ac, actualizar su información
            title = problem_data.get("titleKo", "")
            for lang in ["en", "es"]:
                if f"title{lang.capitalize()}" in problem_data:
                    title = problem_data[f"title{lang.capitalize()}"]
                    break
            
            tier = problem_data.get("level", 0)
            
            tags = []
            for tag in problem_data.get("tags", []):
                tag_name = tag.get("key", "")
                tags.append(tag_name)
            tags_str = ",".join(tags)
            
            solved_count = problem_data.get("solved", 0)
            level = problem_data.get("level", 0)
            accepted_user_count = problem_data.get("acceptedUserCount", 0)
            average_tries = problem_data.get("averageTries", 0.0)
            
            # Actualizar en problems si existe, si no, insertarlo
            cursor.execute("SELECT 1 FROM problems WHERE problem_id = ?", (problem_id,))
            if cursor.fetchone():
                cursor.execute(
                    """
                    UPDATE problems 
                    SET problem_title = ?, tier = ?, tags = ?, solved_count = ?,
                        level = ?, accepted_user_count = ?, average_tries = ?
                    WHERE problem_id = ?
                    """,
                    (title, tier, tags_str, solved_count, level, 
                     accepted_user_count, average_tries, problem_id)
                )
            else:
                cursor.execute(
                    """
                    INSERT INTO problems 
                    (problem_id, problem_title, tier, tags, solved_count, level, 
                     accepted_user_count, average_tries) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (problem_id, title, tier, tags_str, solved_count, level, 
                     accepted_user_count, average_tries)
                )
            
            # Actualizar el título en ladder_problems
            cursor.execute(
                """
                UPDATE ladder_problems
                SET problem_title = ?
                WHERE problem_id = ? AND baekjoon_username = ?
                """,
                (title, problem_id, baekjoon_username)
            )
            
            print(f"Problema {problem_id} actualizado: {title}")
            problems_fixed += 1
            
        else:
            # El problema no existe en Solved.ac, reemplazarlo
            print(f"Problema {problem_id} no encontrado en Solved.ac, buscando reemplazo...")
            
            # Buscar un problema válido para reemplazar
            cursor.execute(
                """
                SELECT p.problem_id, p.problem_title
                FROM problems p
                LEFT JOIN ladder_problems lp ON p.problem_id = lp.problem_id AND lp.baekjoon_username = ?
                WHERE lp.id IS NULL
                AND p.tier IS NOT NULL
                ORDER BY p.tier
                LIMIT 1
                """,
                (baekjoon_username,)
            )
            
            valid_problem = cursor.fetchone()
            
            if valid_problem:
                valid_problem_id = valid_problem["problem_id"]
                valid_problem_title = valid_problem["problem_title"]
                
                # Actualizar el problema en el ladder
                cursor.execute(
                    """
                    UPDATE ladder_problems
                    SET problem_id = ?, problem_title = ?
                    WHERE problem_id = ? AND baekjoon_username = ?
                    """,
                    (valid_problem_id, valid_problem_title, problem_id, baekjoon_username)
                )
                
                print(f"Problema {problem_id} reemplazado por {valid_problem_id}: {valid_problem_title}")
                problems_replaced += 1
                
                # Verificar si el problema inválido está en la tabla problems y eliminarlo
                cursor.execute("SELECT 1 FROM problems WHERE problem_id = ?", (problem_id,))
                if cursor.fetchone():
                    cursor.execute("DELETE FROM problems WHERE problem_id = ?", (problem_id,))
            else:
                print(f"No se encontró un problema válido para reemplazar {problem_id}")
        
        # Guardar cambios después de cada problema procesado
        conn.commit()
        
        # Esperar un poco para no sobrecargar la API
        time.sleep(0.5)
    
    print(f"\nResumen: {problems_fixed} problemas actualizados, {problems_replaced} problemas reemplazados")
    
    conn.close()
    return True

if __name__ == "__main__":
    fix_all_problems() 