import sqlite3

def fix_invalid_problem(invalid_problem_id, baekjoon_username):
    """
    Reemplaza un problema inválido en el ladder de un usuario por uno válido de la base de datos
    
    Args:
        invalid_problem_id: ID del problema inválido
        baekjoon_username: Nombre de usuario de Baekjoon
    """
    print(f"Reemplazando problema inválido {invalid_problem_id} para el usuario {baekjoon_username}...")
    
    # Conectar a la base de datos
    conn = sqlite3.connect('app.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Obtener información del problema inválido en el ladder
    cursor.execute(
        """
        SELECT id, position, state
        FROM ladder_problems
        WHERE problem_id = ? AND baekjoon_username = ?
        """,
        (invalid_problem_id, baekjoon_username)
    )
    
    invalid_ladder_problem = cursor.fetchone()
    
    if not invalid_ladder_problem:
        print(f"No se encontró el problema {invalid_problem_id} en el ladder de {baekjoon_username}")
        conn.close()
        return False
    
    ladder_problem_id = invalid_ladder_problem["id"]
    position = invalid_ladder_problem["position"]
    state = invalid_ladder_problem["state"]
    
    print(f"Problema encontrado en la posición {position} con estado {state}")
    
    # Buscar un problema válido de la base de datos que no esté en el ladder del usuario
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
    
    if not valid_problem:
        print("No se encontró un problema válido para reemplazar")
        conn.close()
        return False
    
    valid_problem_id = valid_problem["problem_id"]
    valid_problem_title = valid_problem["problem_title"]
    
    print(f"Se utilizará el problema {valid_problem_id}: {valid_problem_title} como reemplazo")
    
    # Actualizar el problema en el ladder
    cursor.execute(
        """
        UPDATE ladder_problems
        SET problem_id = ?, problem_title = ?
        WHERE id = ?
        """,
        (valid_problem_id, valid_problem_title, ladder_problem_id)
    )
    
    conn.commit()
    
    print(f"Problema inválido {invalid_problem_id} reemplazado por {valid_problem_id}: {valid_problem_title}")
    
    # Verificar si el problema inválido está en la base de datos 'problems'
    cursor.execute("SELECT 1 FROM problems WHERE problem_id = ?", (invalid_problem_id,))
    if cursor.fetchone():
        # Si existe, eliminarlo
        cursor.execute("DELETE FROM problems WHERE problem_id = ?", (invalid_problem_id,))
        conn.commit()
        print(f"Problema inválido {invalid_problem_id} eliminado de la base de datos de problemas")
    
    conn.close()
    return True

if __name__ == "__main__":
    # Datos del problema y usuario a corregir
    invalid_problem_id = "20356"
    baekjoon_username = "fischer"  # Ajustar si es necesario
    
    fix_invalid_problem(invalid_problem_id, baekjoon_username) 