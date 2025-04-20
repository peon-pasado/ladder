import sqlite3
import random
import math
from datetime import datetime, timedelta

class ProblemRecommender:
    """
    Sistema de recomendación para seleccionar el siguiente problema a revelar
    basado en el rating del usuario y un sistema tipo buchholz.
    """
    
    # Rango de nivel óptimo (+-offset alrededor del rating del usuario)
    LEVEL_RANGE_OFFSET = 250
    
    # Factor para calcular el buchholz
    BUCHHOLZ_WEIGHT = 0.3
    
    @staticmethod
    def calculate_buchholz(user_id):
        """
        Calcula un valor tipo buchholz para el usuario basado en 
        los niveles de los problemas resueltos recientemente.
        
        Args:
            user_id: ID del usuario
            
        Returns:
            Valor buchholz calculado (valor positivo o negativo)
        """
        conn = sqlite3.connect('app.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Obtener los últimos 5 problemas resueltos con sus niveles
        cursor.execute('''
            SELECT p.level 
            FROM solved_problems sp
            JOIN problems p ON sp.problem_id = p.problem_id
            WHERE sp.user_id = ?
            ORDER BY sp.solved_at DESC
            LIMIT 5
        ''', (user_id,))
        
        problems = cursor.fetchall()
        conn.close()
        
        if not problems:
            return 0
        
        # Calcular el promedio del nivel de los problemas recientes, ignorando valores nulos o cero
        valid_levels = [p['level'] for p in problems if p['level'] is not None and p['level'] > 0]
        
        if not valid_levels:
            return 0  # Si no hay niveles válidos, retornar 0
            
        avg_level = sum(valid_levels) / len(valid_levels)
        
        # Obtener el rating actual del usuario
        conn = sqlite3.connect('app.db')
        cursor = conn.cursor()
        cursor.execute("SELECT rating FROM users WHERE id = ?", (user_id,))
        user_data = cursor.fetchone()
        conn.close()
        
        user_rating = user_data[0] if user_data else 1500
        
        # Calcular el buchholz (diferencia respecto al rating)
        # Si es positivo, el usuario está resolviendo problemas por encima de su nivel
        # Si es negativo, el usuario está resolviendo problemas por debajo de su nivel
        buchholz = avg_level - user_rating
        
        # Limitar el valor del buchholz para evitar valores extremos
        # Usando un límite de ±500 para mantenerlo razonable
        MAX_BUCHHOLZ = 500
        buchholz = max(-MAX_BUCHHOLZ, min(MAX_BUCHHOLZ, buchholz))
        
        return buchholz
    
    @staticmethod
    def reveal_next_problem(user_id, baekjoon_username):
        """
        Selecciona y añade el siguiente problema recomendado basado en el rating actual
        
        Args:
            user_id: ID del usuario
            baekjoon_username: Nombre de usuario de Baekjoon
            
        Returns:
            ID del problema revelado o None si no hay más problemas
        """
        # Obtener la próxima posición para el ladder
        conn = sqlite3.connect('app.db')
        cursor = conn.cursor()
        
        cursor.execute(
            """
            SELECT MAX(position) 
            FROM ladder_problems
            WHERE baekjoon_username = ?
            """,
            (baekjoon_username,)
        )
        
        result = cursor.fetchone()
        next_position = (result[0] or 0) + 1
        
        # Obtener el rating actual del usuario
        cursor.execute("SELECT rating FROM users WHERE id = ?", (user_id,))
        user_data = cursor.fetchone()
        user_rating = user_data[0] if user_data else 1500
        
        # Calcular el buchholz del usuario
        buchholz = ProblemRecommender.calculate_buchholz(user_id)
        
        # Ajustar el rating objetivo según el buchholz
        target_rating = user_rating + (buchholz * ProblemRecommender.BUCHHOLZ_WEIGHT)
        
        # Rango de niveles a buscar
        min_level = int(target_rating - ProblemRecommender.LEVEL_RANGE_OFFSET)
        max_level = int(target_rating + ProblemRecommender.LEVEL_RANGE_OFFSET)
        
        # Añadir un factor aleatorio al rango para aumentar variedad
        random_offset = random.randint(-50, 50)
        min_level += random_offset
        max_level += random_offset
        
        # Obtener problemas que ya están en el ladder para excluirlos
        cursor.execute(
            """
            SELECT problem_id 
            FROM ladder_problems
            WHERE baekjoon_username = ?
            """,
            (baekjoon_username,)
        )
        
        existing_problems = [row[0] for row in cursor.fetchall()]
        
        # Buscar un nuevo problema en la base de datos general
        cursor.execute(
            """
            SELECT problem_id, problem_title, level
            FROM problems 
            WHERE level BETWEEN ? AND ?
            AND problem_id NOT IN ({})
            ORDER BY RANDOM()
            LIMIT 10
            """.format(','.join(['?'] * len(existing_problems)) if existing_problems else 'NULL'),
            [min_level, max_level] + existing_problems if existing_problems else [min_level, max_level]
        )
        
        candidates = cursor.fetchall()
        
        if candidates:
            # Seleccionar un problema aleatorio
            selected = random.choice(candidates)
            problem_id = selected[0]
            problem_title = selected[1]
            
            # Insertar el nuevo problema en el ladder como 'current'
            cursor.execute(
                """
                INSERT INTO ladder_problems 
                (baekjoon_username, position, problem_id, problem_title, state) 
                VALUES (?, ?, ?, ?, ?)
                """,
                (baekjoon_username, next_position, problem_id, problem_title, 'current')
            )
            
            # Obtener el ID del problema recién insertado
            cursor.execute(
                """
                SELECT id FROM ladder_problems
                WHERE baekjoon_username = ? AND problem_id = ? AND position = ?
                """,
                (baekjoon_username, problem_id, next_position)
            )
            
            new_problem_id = cursor.fetchone()[0]
            conn.commit()
            conn.close()
            
            return new_problem_id
        
        # Si no hay candidatos en el rango ideal, ampliar la búsqueda
        wider_min_level = int(target_rating - ProblemRecommender.LEVEL_RANGE_OFFSET * 2)
        wider_max_level = int(target_rating + ProblemRecommender.LEVEL_RANGE_OFFSET * 2)
        
        cursor.execute(
            """
            SELECT problem_id, problem_title, level
            FROM problems 
            WHERE level BETWEEN ? AND ?
            AND problem_id NOT IN ({})
            ORDER BY RANDOM()
            LIMIT 5
            """.format(','.join(['?'] * len(existing_problems)) if existing_problems else 'NULL'),
            [wider_min_level, wider_max_level] + existing_problems if existing_problems else [wider_min_level, wider_max_level]
        )
        
        wider_candidates = cursor.fetchall()
        
        if wider_candidates:
            # Seleccionar un problema aleatorio
            selected = random.choice(wider_candidates)
            problem_id = selected[0]
            problem_title = selected[1]
            
            # Insertar el nuevo problema en el ladder como 'current'
            cursor.execute(
                """
                INSERT INTO ladder_problems 
                (baekjoon_username, position, problem_id, problem_title, state) 
                VALUES (?, ?, ?, ?, ?)
                """,
                (baekjoon_username, next_position, problem_id, problem_title, 'current')
            )
            
            # Obtener el ID del problema recién insertado
            cursor.execute(
                """
                SELECT id FROM ladder_problems
                WHERE baekjoon_username = ? AND problem_id = ? AND position = ?
                """,
                (baekjoon_username, problem_id, next_position)
            )
            
            new_problem_id = cursor.fetchone()[0]
            conn.commit()
            conn.close()
            
            return new_problem_id
        
        # Si aún no hay candidatos, buscar cualquier problema no usado
        cursor.execute(
            """
            SELECT problem_id, problem_title
            FROM problems 
            WHERE problem_id NOT IN ({})
            ORDER BY RANDOM()
            LIMIT 1
            """.format(','.join(['?'] * len(existing_problems)) if existing_problems else 'NULL'),
            existing_problems if existing_problems else []
        )
        
        fallback = cursor.fetchone()
        
        if fallback:
            # Usar cualquier problema disponible
            problem_id = fallback[0]
            problem_title = fallback[1]
            
            # Insertar el nuevo problema en el ladder como 'current'
            cursor.execute(
                """
                INSERT INTO ladder_problems 
                (baekjoon_username, position, problem_id, problem_title, state) 
                VALUES (?, ?, ?, ?, ?)
                """,
                (baekjoon_username, next_position, problem_id, problem_title, 'current')
            )
            
            # Obtener el ID del problema recién insertado
            cursor.execute(
                """
                SELECT id FROM ladder_problems
                WHERE baekjoon_username = ? AND problem_id = ? AND position = ?
                """,
                (baekjoon_username, problem_id, next_position)
            )
            
            new_problem_id = cursor.fetchone()[0]
            conn.commit()
            conn.close()
            
            return new_problem_id
            
        conn.close()
        return None 