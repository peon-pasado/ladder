from app.utils.solved_ac_api import SolvedAcAPI

def validate_problem(problem_id):
    """
    Verifica que un problema exista en Baekjoon antes de agregarlo a la base de datos.
    
    Args:
        problem_id: ID del problema a verificar
        
    Returns:
        dict: Información del problema si existe
        None: Si el problema no existe o no se puede obtener información
    """
    # Intentar obtener información del problema desde Solved.ac
    problem_data = SolvedAcAPI.get_problem_by_id(problem_id)
    
    if not problem_data:
        return None
    
    # Verificar que tenga al menos un título
    if not problem_data.get("titleKo") and not problem_data.get("titleEn") and not problem_data.get("titleEs"):
        return None
    
    # Verificar que tenga nivel (tier) asignado
    if not problem_data.get("level"):
        return None
    
    return problem_data

def get_problem_info(problem_id):
    """
    Obtiene información formateada de un problema validado
    
    Args:
        problem_id: ID del problema
        
    Returns:
        dict: Información formateada del problema si existe
        None: Si el problema no existe o no tiene información suficiente
    """
    problem_data = validate_problem(problem_id)
    
    if not problem_data:
        return None
    
    # Extraer título
    title = problem_data.get("titleKo", "")
    for lang in ["en", "es"]:
        if f"title{lang.capitalize()}" in problem_data:
            title = problem_data[f"title{lang.capitalize()}"]
            break
    
    # Extraer tier/nivel
    tier = problem_data.get("level", 0)
    
    # Extraer tags
    tags = []
    for tag in problem_data.get("tags", []):
        tag_name = tag.get("key", "")
        tags.append(tag_name)
    tags_str = ",".join(tags)
    
    # Extraer estadísticas
    solved_count = problem_data.get("solved", 0)
    level = problem_data.get("level", 0)
    accepted_user_count = problem_data.get("acceptedUserCount", 0)
    average_tries = problem_data.get("averageTries", 0.0)
    
    return {
        "problem_id": problem_id,
        "title": title,
        "tier": tier,
        "tags": tags_str,
        "level": level,
        "solved_count": solved_count,
        "accepted_user_count": accepted_user_count,
        "average_tries": average_tries
    }

def batch_validate_problems(problem_ids):
    """
    Valida varios problemas a la vez y devuelve solo los válidos
    
    Args:
        problem_ids: Lista de IDs de problemas a validar
        
    Returns:
        list: Lista de IDs de problemas válidos
    """
    valid_problem_ids = []
    
    for problem_id in problem_ids:
        if validate_problem(problem_id):
            valid_problem_ids.append(problem_id)
    
    return valid_problem_ids 