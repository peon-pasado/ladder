import sqlite3
import time
from app.utils.solved_ac_api import SolvedAcAPI

def update_existing_problems_info():
    """
    Actualiza la información de los problemas existentes en la base de datos
    utilizando la API de Solved.ac.
    """
    conn = sqlite3.connect('app.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Obtener todos los IDs de problema de la tabla ladder_problems
    cursor.execute(
        """
        SELECT DISTINCT problem_id FROM ladder_problems
        """
    )
    ladder_problems = {row['problem_id'] for row in cursor.fetchall()}
    
    # También obtener los problemas de la tabla problems que tienen información incompleta
    cursor.execute(
        """
        SELECT problem_id FROM problems 
        WHERE tier IS NULL OR tags IS NULL OR level IS NULL
        """
    )
    incomplete_problems = {row['problem_id'] for row in cursor.fetchall()}
    
    # Combinar ambos conjuntos
    problems_to_update = ladder_problems.union(incomplete_problems)
    
    print(f"Se actualizarán {len(problems_to_update)} problemas")
    
    # Procesar en lotes para no sobrecargar la API
    batch_size = 100
    problem_list = list(problems_to_update)
    
    for i in range(0, len(problem_list), batch_size):
        batch = problem_list[i:i+batch_size]
        print(f"Procesando lote {i//batch_size + 1}/{(len(problem_list)-1)//batch_size + 1} ({len(batch)} problemas)")
        
        # Obtener datos de la API
        try:
            problems_data = SolvedAcAPI.get_problems_by_ids(batch)
            
            if problems_data:
                for problem in problems_data:
                    try:
                        problem_id = str(problem.get("problemId", ""))
                        
                        # Extraer los datos relevantes
                        title = problem.get("titleKo", "")
                        for lang in ["en", "es"]:
                            if f"title{lang.capitalize()}" in problem:
                                title = problem[f"title{lang.capitalize()}"]
                                break
                        
                        tier = problem.get("level", 0)
                        
                        tags = []
                        for tag in problem.get("tags", []):
                            tag_name = tag.get("key", "")
                            tags.append(tag_name)
                        tags_str = ",".join(tags)
                        
                        solved_count = problem.get("solved", 0)
                        level = problem.get("level", 0)
                        accepted_user_count = problem.get("acceptedUserCount", 0)
                        average_tries = problem.get("averageTries", 0.0)
                        
                        # Intentar actualizar primero
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
                        
                        # Si no existe, insertar
                        if cursor.rowcount == 0:
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
                            
                        # También actualizar el título en ladder_problems si es necesario
                        cursor.execute(
                            """
                            UPDATE ladder_problems
                            SET problem_title = ?
                            WHERE problem_id = ?
                            """,
                            (title, problem_id)
                        )
                        
                    except sqlite3.IntegrityError:
                        print(f"Error al actualizar/insertar problema {problem_id}")
                    except Exception as e:
                        print(f"Error al procesar problema {problem_id}: {str(e)}")
            
            # Guardar los cambios después de cada lote
            conn.commit()
            
        except Exception as e:
            print(f"Error al obtener datos del lote: {str(e)}")
        
        # Esperar un poco entre lotes para no sobrecargar la API
        time.sleep(1)
    
    # Verificar problemas que no se pudieron actualizar
    cursor.execute(
        """
        SELECT problem_id FROM problems 
        WHERE tier IS NULL OR tags IS NULL OR level IS NULL
        """
    )
    still_incomplete = cursor.fetchall()
    
    if still_incomplete:
        print(f"Hay {len(still_incomplete)} problemas con información incompleta:")
        for row in still_incomplete[:10]:  # Mostrar solo los primeros 10
            print(f"  - Problema {row['problem_id']}")
        if len(still_incomplete) > 10:
            print(f"  ... y {len(still_incomplete) - 10} más")
    else:
        print("Todos los problemas tienen información completa")
    
    conn.close()
    print("Proceso de actualización completado")

if __name__ == "__main__":
    update_existing_problems_info() 