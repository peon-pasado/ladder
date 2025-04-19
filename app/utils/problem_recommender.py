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
    def get_next_problem(user_id, baekjoon_username):
        """
        Recomienda el siguiente problema a revelar basado en el rating
        del usuario y el valor buchholz.
        
        Args:
            user_id: ID del usuario
            baekjoon_username: Nombre de usuario de Baekjoon
            
        Returns:
            ID del problema recomendado o None si no hay recomendaciones
        """
        conn = sqlite3.connect('app.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Obtener el rating actual del usuario
        cursor.execute("SELECT rating FROM users WHERE id = ?", (user_id,))
        user_data = cursor.fetchone()
        user_rating = user_data[0] if user_data else 1500
        
        # Calcular el buchholz del usuario
        buchholz = ProblemRecommender.calculate_buchholz(user_id)
        
        # Ajustar el rating objetivo según el buchholz
        # Si el buchholz es positivo (el usuario resuelve problemas más difíciles),
        # aumentamos el nivel recomendado. Si es negativo, lo reducimos.
        target_rating = user_rating + (buchholz * ProblemRecommender.BUCHHOLZ_WEIGHT)
        
        # Rango de niveles a buscar (+-LEVEL_RANGE_OFFSET alrededor del rating objetivo)
        min_level = int(target_rating - ProblemRecommender.LEVEL_RANGE_OFFSET)
        max_level = int(target_rating + ProblemRecommender.LEVEL_RANGE_OFFSET)
        
        # Añadir un factor aleatorio al rango para aumentar variedad
        random_offset = random.randint(-50, 50)
        min_level += random_offset
        max_level += random_offset
        
        # Primero obtener el número total de problemas que cumplen con el criterio
        cursor.execute('''
            SELECT COUNT(*)
            FROM ladder_problems lp
            JOIN problems p ON lp.problem_id = p.problem_id
            WHERE lp.baekjoon_username = ? 
            AND lp.state = 'hidden'
            AND p.level BETWEEN ? AND ?
        ''', (baekjoon_username, min_level, max_level))
        
        total_problems = cursor.fetchone()[0]
        
        if total_problems > 0:
            # Si hay problemas disponibles, seleccionar un grupo aleatorio
            # Añadir offset aleatorio para obtener diferentes resultados cada vez
            random_offset = random.randint(0, max(0, total_problems - 1))
            
            # Limitar el número de resultados a considerar para evitar sesgo hacia niveles específicos
            limit = min(10, total_problems)
            
            cursor.execute('''
                SELECT lp.id, lp.problem_id, p.level
                FROM ladder_problems lp
                JOIN problems p ON lp.problem_id = p.problem_id
                WHERE lp.baekjoon_username = ? 
                AND lp.state = 'hidden'
                AND p.level BETWEEN ? AND ?
                ORDER BY RANDOM()
                LIMIT ?
            ''', (baekjoon_username, min_level, max_level, limit))
            
            candidate_problems = cursor.fetchall()
            conn.close()
            
            if candidate_problems:
                # Elegir un problema aleatorio de los candidatos
                selected_problem = random.choice(candidate_problems)
                return selected_problem['id']
        
        # Si no hay problemas en el rango ideal, buscar problemas ocultos con un rango más amplio
        conn = sqlite3.connect('app.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Ampliar el rango de búsqueda
        wider_min_level = int(target_rating - ProblemRecommender.LEVEL_RANGE_OFFSET * 2)
        wider_max_level = int(target_rating + ProblemRecommender.LEVEL_RANGE_OFFSET * 2)
        
        cursor.execute('''
            SELECT lp.id, lp.problem_id
            FROM ladder_problems lp
            JOIN problems p ON lp.problem_id = p.problem_id
            WHERE lp.baekjoon_username = ? 
            AND lp.state = 'hidden'
            AND p.level BETWEEN ? AND ?
            ORDER BY RANDOM()
            LIMIT 5
        ''', (baekjoon_username, wider_min_level, wider_max_level))
        
        wider_candidates = cursor.fetchall()
        
        if wider_candidates:
            # Si encontramos candidatos en el rango ampliado
            selected_problem = random.choice(wider_candidates)
            conn.close()
            return selected_problem['id']
        
        # Si aún no hay candidatos, buscar cualquier problema oculto
        cursor.execute('''
            SELECT lp.id, lp.problem_id
            FROM ladder_problems lp
            WHERE lp.baekjoon_username = ? 
            AND lp.state = 'hidden'
            ORDER BY RANDOM()
            LIMIT 5
        ''', (baekjoon_username,))
        
        fallback_problems = cursor.fetchall()
        
        if not fallback_problems:
            conn.close()
            return None
            
        # Seleccionar un problema aleatorio entre los disponibles
        selected_problem = random.choice(fallback_problems)
        conn.close()
        return selected_problem['id']
    
    @staticmethod
    def reveal_next_problem(user_id, baekjoon_username):
        """
        Revela el siguiente problema recomendado basado en el rating actual
        
        Args:
            user_id: ID del usuario
            baekjoon_username: Nombre de usuario de Baekjoon
            
        Returns:
            ID del problema revelado o None si no hay más problemas
        """
        problem_id = ProblemRecommender.get_next_problem(user_id, baekjoon_username)
        
        if not problem_id:
            return None
        
        # Actualizar el estado del problema a 'current', pero sin revealed_at
        # El revealed_at se establecerá cuando el usuario interactúe con el problema
        conn = sqlite3.connect('app.db')
        cursor = conn.cursor()
        
        cursor.execute(
            "UPDATE ladder_problems SET state = 'current' WHERE id = ?",
            (problem_id,)
        )
        
        conn.commit()
        conn.close()
        
        return problem_id 