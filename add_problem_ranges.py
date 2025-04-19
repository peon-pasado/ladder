import sqlite3
import requests
import time
from app.models.ladder_problem import LadderProblem
from app.utils.solved_ac_api import SolvedAcAPI
from app.utils.problem_validator import validate_problem, get_problem_info

def add_problem_ranges():
    """
    Agrega los rangos de problemas especificados a la base de datos.
    Los problemas se añaden como registros individuales con información de Solved.ac.
    Solo se agregarán los problemas que existan en Baekjoon.
    """
    # Rangos de problemas a agregar
    problem_ranges = [
        (20996, 21008),  # Rango 1
        (21060, 21071),  # Rango 2
        (20329, 20329),  # Solo el problema 20329
        (21048, 21048),  # Solo el problema 21048
        (20339, 20339),  # Solo el problema 20339
        (21050, 21058),  # Rango del 21050 al 21058
        (21072, 21132),  # Rango 4
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
    
    conn.close()

def add_problems_by_tier(tier_range=(1, 5), problems_per_tier=20):
    """
    Agrega problemas por nivel de dificultad (tier) usando la API de Solved.ac
    
    Args:
        tier_range: Tupla con el rango de tiers a agregar (min, max)
        problems_per_tier: Número de problemas a agregar por cada tier
    """
    conn = sqlite3.connect('app.db')
    cursor = conn.cursor()
    
    # Asegurarse de que la tabla 'problems' existe
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
    
    total_added = 0
    
    # Para cada tier en el rango
    for tier in range(tier_range[0], tier_range[1] + 1):
        print(f"Buscando problemas de tier {tier}...")
        
        # Obtener problemas de la API (estos ya están validados al venir de la API)
        problems = SolvedAcAPI.get_problems_by_tier(tier, page=1, sort="solved", direction="desc")
        
        if not problems:
            print(f"No se encontraron problemas para el tier {tier}")
            continue
        
        # Filtrar los que no existen en la BD y limitar al número solicitado
        new_problems = []
        for problem in problems:
            problem_id = str(problem.get("problemId", ""))
            if problem_id not in existing_problems:
                new_problems.append(problem)
                if len(new_problems) >= problems_per_tier:
                    break
        
        print(f"Se añadirán {len(new_problems)} problemas nuevos de tier {tier}")
        
        # Insertar los nuevos problemas
        for problem in new_problems:
            try:
                problem_id = str(problem.get("problemId", ""))
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
                
                total_added += 1
                
            except sqlite3.IntegrityError:
                print(f"Error al insertar problema {problem_id}")
        
        # Esperar un poco entre tiers
        time.sleep(1)
    
    # Guardar cambios
    conn.commit()
    
    print(f"Se añadieron {total_added} problemas en total")
    
    conn.close()

if __name__ == "__main__":
    # Primero agregar problemas por rangos
    add_problem_ranges()
    
    # Luego agregar problemas por tiers (niveles de dificultad)
    add_problems_by_tier(tier_range=(1, 10), problems_per_tier=10) 