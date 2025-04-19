import sqlite3
import time
import sys
from app.utils.problem_validator import validate_problem, get_problem_info, batch_validate_problems

def add_validated_problems(problem_ids):
    """
    Agrega problemas a la base de datos solo si existen en Baekjoon.
    
    Args:
        problem_ids: Lista de IDs de problemas a verificar y agregar
    """
    print(f"Validando {len(problem_ids)} problemas...")
    
    # Conectar a la base de datos
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
    
    # Filtrar solo los problemas que no existen en la base de datos
    new_problem_ids = [pid for pid in problem_ids if pid not in existing_problems]
    
    if not new_problem_ids:
        print("Todos los problemas ya existen en la base de datos.")
        conn.close()
        return
    
    print(f"Validando {len(new_problem_ids)} problemas nuevos...")
    
    valid_problems = 0
    invalid_problems = 0
    
    # Procesar cada problema
    for problem_id in new_problem_ids:
        print(f"Validando problema {problem_id}...", end=" ")
        
        # Obtener información del problema
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
    
    conn.close()

def ask_for_problem_ids():
    """Solicita al usuario que ingrese IDs de problemas"""
    print("Ingrese los IDs de problemas separados por espacios:")
    input_line = input()
    return [id.strip() for id in input_line.split() if id.strip()]

if __name__ == "__main__":
    # Si se proporcionan IDs como argumentos, usarlos
    if len(sys.argv) > 1:
        problem_ids = sys.argv[1:]
    else:
        # Si no hay argumentos, solicitar al usuario
        problem_ids = ask_for_problem_ids()
    
    if problem_ids:
        add_validated_problems(problem_ids)
    else:
        print("No se proporcionaron IDs de problemas.")
        print("Uso: python add_validated_problems.py [problem_id1 problem_id2 ...]")
        print("O ejecute el script sin argumentos para introducir los IDs manualmente.") 