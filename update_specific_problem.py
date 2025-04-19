import sqlite3
import time
from app.utils.solved_ac_api import SolvedAcAPI

def update_specific_problem(problem_id):
    """
    Actualiza la información de un problema específico utilizando la API de Solved.ac
    
    Args:
        problem_id: ID del problema a actualizar
    """
    print(f"Actualizando información del problema {problem_id}...")
    
    # Conectar a la base de datos
    conn = sqlite3.connect('app.db')
    cursor = conn.cursor()
    
    # Obtener información del problema desde Solved.ac
    problem_data = SolvedAcAPI.get_problem_by_id(problem_id)
    
    if not problem_data:
        print(f"No se pudo obtener información para el problema {problem_id} desde Solved.ac")
        return False
    
    # Extraer los datos relevantes
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
    
    # Verificar si el problema existe en la base de datos
    cursor.execute("SELECT 1 FROM problems WHERE problem_id = ?", (problem_id,))
    exists = cursor.fetchone()
    
    if exists:
        # Actualizar el problema existente
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
        print(f"Se actualizó el problema {problem_id}: {title}")
    else:
        # Insertar el problema como nuevo
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
        print(f"Se insertó el problema {problem_id}: {title}")
    
    # Actualizar también el título en la tabla ladder_problems si existe
    cursor.execute(
        """
        UPDATE ladder_problems
        SET problem_title = ?
        WHERE problem_id = ?
        """,
        (title, problem_id)
    )
    
    cursor.execute("SELECT baekjoon_username FROM ladder_problems WHERE problem_id = ?", (problem_id,))
    users = cursor.fetchall()
    if users:
        usernames = [user[0] for user in users]
        print(f"El problema {problem_id} está en el ladder de los usuarios: {', '.join(usernames)}")
    
    # Guardar cambios
    conn.commit()
    conn.close()
    
    return True

if __name__ == "__main__":
    # Actualizar el problema específico
    problem_id = "20356"
    update_specific_problem(problem_id) 