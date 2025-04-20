import sqlite3
import requests
from app.models.solved_problem import SolvedProblem
from app.utils.solved_ac_api import SolvedAcAPI
from app.utils.rating_calculator import RatingCalculator
from app.models.user import User
from app.utils.problem_recommender import ProblemRecommender

class LadderProblem:
    def __init__(self, id, baekjoon_username, position, problem_id, problem_title, state, 
                tier=None, tags=None, level=None, solved_count=0, accepted_user_count=0, average_tries=0.0, revealed_at=None):
        self.id = id
        self.baekjoon_username = baekjoon_username
        self.position = position
        self.problem_id = problem_id
        self.problem_title = problem_title
        self.state = state  # 'hidden', 'current', 'solved', 'unsolved'
        
        # Datos adicionales de Solved.ac
        self.tier = tier
        self.tags = tags
        self.level = level
        self.solved_count = solved_count
        self.accepted_user_count = accepted_user_count
        self.average_tries = average_tries
        self.revealed_at = revealed_at
    
    @staticmethod
    def get_ladder_problems(baekjoon_username):
        """Obtener todos los problemas del ladder para un nombre de usuario de Baekjoon"""
        conn = sqlite3.connect('app.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute(
            """
            SELECT lp.*, p.tier, p.tags, p.level, p.solved_count, 
                   p.accepted_user_count, p.average_tries
            FROM ladder_problems lp
            LEFT JOIN problems p ON lp.problem_id = p.problem_id
            WHERE lp.baekjoon_username = ? 
            ORDER BY lp.position ASC
            """,
            (baekjoon_username,)
        )
        
        problems = []
        for problem_data in cursor.fetchall():
            revealed_at = problem_data['revealed_at'] if 'revealed_at' in problem_data else None
            problems.append(LadderProblem(
                id=problem_data['id'],
                baekjoon_username=problem_data['baekjoon_username'],
                position=problem_data['position'],
                problem_id=problem_data['problem_id'],
                problem_title=problem_data['problem_title'],
                state=problem_data['state'],
                tier=problem_data['tier'] if 'tier' in problem_data and problem_data['tier'] is not None else None,
                tags=problem_data['tags'] if 'tags' in problem_data and problem_data['tags'] is not None else None,
                level=problem_data['level'] if 'level' in problem_data and problem_data['level'] is not None else None,
                solved_count=problem_data['solved_count'] if 'solved_count' in problem_data and problem_data['solved_count'] is not None else 0,
                accepted_user_count=problem_data['accepted_user_count'] if 'accepted_user_count' in problem_data and problem_data['accepted_user_count'] is not None else 0,
                average_tries=problem_data['average_tries'] if 'average_tries' in problem_data and problem_data['average_tries'] is not None else 0.0,
                revealed_at=revealed_at
            ))
        
        conn.close()
        return problems
    
    @staticmethod
    def get_problem_by_id(ladder_problem_id):
        """Obtener un problema específico del ladder por su ID"""
        conn = sqlite3.connect('app.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute(
            """
            SELECT lp.*, p.tier, p.tags, p.level, p.solved_count, 
                   p.accepted_user_count, p.average_tries
            FROM ladder_problems lp
            LEFT JOIN problems p ON lp.problem_id = p.problem_id
            WHERE lp.id = ?
            """,
            (ladder_problem_id,)
        )
        
        problem_data = cursor.fetchone()
        if not problem_data:
            conn.close()
            return None
        
        problem = LadderProblem(
            id=problem_data['id'],
            baekjoon_username=problem_data['baekjoon_username'],
            position=problem_data['position'],
            problem_id=problem_data['problem_id'],
            problem_title=problem_data['problem_title'],
            state=problem_data['state'],
            tier=problem_data['tier'] if 'tier' in problem_data and problem_data['tier'] is not None else None,
            tags=problem_data['tags'] if 'tags' in problem_data and problem_data['tags'] is not None else None,
            level=problem_data['level'] if 'level' in problem_data and problem_data['level'] is not None else None,
            solved_count=problem_data['solved_count'] if 'solved_count' in problem_data and problem_data['solved_count'] is not None else 0,
            accepted_user_count=problem_data['accepted_user_count'] if 'accepted_user_count' in problem_data and problem_data['accepted_user_count'] is not None else 0,
            average_tries=problem_data['average_tries'] if 'average_tries' in problem_data and problem_data['average_tries'] is not None else 0.0
        )
        
        conn.close()
        return problem
    
    @staticmethod
    def initialize_ladder(baekjoon_username, problems_data):
        """Inicializar el ladder con problemas para un nombre de usuario de Baekjoon"""
        conn = sqlite3.connect('app.db')
        cursor = conn.cursor()
        
        # Primero obtener el user_id del baekjoon_username
        cursor.execute(
            "SELECT user_id FROM baekjoon_accounts WHERE baekjoon_username = ? LIMIT 1",
            (baekjoon_username,)
        )
        
        account_data = cursor.fetchone()
        user_id = account_data[0] if account_data else None
        
        # Solo insertar el primer problema como 'current'
        if problems_data and len(problems_data) > 0:
            first_problem = problems_data[0]
            cursor.execute(
                """
                INSERT INTO ladder_problems 
                (baekjoon_username, position, problem_id, problem_title, state) 
                VALUES (?, ?, ?, ?, ?)
                """,
                (baekjoon_username, 1, first_problem['id'], first_problem['title'], 'current')
            )
            conn.commit()
        
        conn.close()
        
        return True
    
    @staticmethod
    def update_problem_state(problem_id, new_state):
        """Actualizar el estado de un problema del ladder"""
        conn = sqlite3.connect('app.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Primero obtenemos información del problema para tener todos los datos necesarios
        cursor.execute(
            """
            SELECT lp.* 
            FROM ladder_problems lp
            WHERE lp.id = ?
            """,
            (problem_id,)
        )
        
        problem_data = cursor.fetchone()
        
        # Si el estado nuevo es 'current', actualizamos revealed_at con la hora actual
        if new_state == 'current':
            from datetime import datetime, timedelta
            # Usar una hora 6 horas en el futuro para dar más tiempo
            future_time = datetime.now() + timedelta(hours=6)
            # Formato sin Z para evitar problemas de zona horaria en JavaScript
            current_time = future_time.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3]
            cursor.execute(
                "UPDATE ladder_problems SET state = ?, revealed_at = ? WHERE id = ?",
                (new_state, current_time, problem_id)
            )
        else:
            # Actualizamos solo el estado
            cursor.execute(
                "UPDATE ladder_problems SET state = ? WHERE id = ?",
                (new_state, problem_id)
            )
        
        # Si el problema está siendo marcado como resuelto, lo guardamos en solved_problems
        if new_state == 'solved' and problem_data:
            # Necesitamos obtener el user_id del usuario que está marcando el problema como resuelto
            # Para esto, necesitamos que la función sea llamada con el user_id como parámetro adicional
            # En las llamadas sucesivas, modificaremos esta parte
            problem_id_value = problem_data['problem_id']
            problem_title = problem_data['problem_title']
            position = problem_data['position']
        
        conn.commit()
        conn.close()
        return cursor.rowcount > 0
    
    @staticmethod
    def save_solved_problem(user_id, problem_id, problem_title, position):
        """
        Guarda un problema resuelto para un usuario específico y actualiza su rating
        
        Args:
            user_id: ID del usuario que resolvió el problema
            problem_id: ID del problema en Baekjoon
            problem_title: Título del problema
            position: Posición del problema en el ladder
        """
        # Guardar el problema en solved_problems
        SolvedProblem.save_solved_problem(
            user_id, 
            problem_id, 
            problem_title, 
            position
        )
        
        # Obtener el nivel del problema y el rating actual del usuario
        conn = sqlite3.connect('app.db')
        cursor = conn.cursor()
        
        # Obtener el nivel del problema
        cursor.execute(
            "SELECT level FROM problems WHERE problem_id = ?",
            (problem_id,)
        )
        problem_data = cursor.fetchone()
        problem_level = problem_data[0] if problem_data and problem_data[0] is not None else 1500
        
        # Obtener el rating actual del usuario
        cursor.execute(
            "SELECT rating FROM users WHERE id = ?",
            (user_id,)
        )
        user_data = cursor.fetchone()
        current_rating = user_data[0] if user_data else 1500
        
        # Obtener el nombre de usuario de Baekjoon del usuario para revelar el siguiente problema
        cursor.execute(
            "SELECT baekjoon_username FROM baekjoon_accounts WHERE user_id = ? LIMIT 1",
            (user_id,)
        )
        account_data = cursor.fetchone()
        
        conn.close()
        
        # Calcular el cambio de rating basado en la fórmula
        delta_rating = RatingCalculator.calculate_rating_change(current_rating, problem_level)
        
        # Actualizar el rating del usuario
        User.update_rating(user_id, delta_rating)
        
        # Si tenemos el nombre de usuario de Baekjoon, revelar el siguiente problema recomendado
        if account_data:
            baekjoon_username = account_data[0]
            # Usar el recomendador para revelar el siguiente problema basado en el rating y buchholz
            ProblemRecommender.reveal_next_problem(user_id, baekjoon_username)
        
        return True
    
    @staticmethod
    def clear_ladder(baekjoon_username):
        """Eliminar todos los problemas del ladder para un nombre de usuario de Baekjoon"""
        conn = sqlite3.connect('app.db')
        cursor = conn.cursor()
        
        # Eliminar todos los problemas del ladder
        cursor.execute(
            "DELETE FROM ladder_problems WHERE baekjoon_username = ?",
            (baekjoon_username,)
        )
        
        conn.commit()
        conn.close()
        return cursor.rowcount > 0
    
    @staticmethod
    def get_sample_problems():
        """Obtener una lista de problemas de ejemplo para inicializar el ladder"""
        # Obtener problemas de la base de datos
        conn = sqlite3.connect('app.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Seleccionar problemas de manera aleatoria
        cursor.execute(
            """
            SELECT problem_id, problem_title 
            FROM problems 
            ORDER BY RANDOM()
            LIMIT 50
            """
        )
        
        sample_problems = []
        for row in cursor.fetchall():
            sample_problems.append({
                "id": row["problem_id"],
                "title": row["problem_title"]
            })
            
        conn.close()
        
        # Si no hay problemas en la base de datos, usar lista predefinida
        if not sample_problems:
            return [
                {"id": "1000", "title": "A+B"},
                {"id": "1001", "title": "A-B"},
                {"id": "1008", "title": "A/B"},
                {"id": "2557", "title": "Hello World"},
                {"id": "2558", "title": "A+B - 2"},
                {"id": "10998", "title": "A×B"},
                {"id": "10869", "title": "Operaciones Aritméticas"},
                {"id": "9498", "title": "Notas de Examen"},
                {"id": "2753", "title": "Año Bisiesto"},
                {"id": "14681", "title": "Seleccionar Cuadrante"},
                {"id": "2884", "title": "Despertador"},
                {"id": "2739", "title": "Tabla de Multiplicar"},
                {"id": "10950", "title": "A+B - 3"},
                {"id": "8393", "title": "Suma"},
                {"id": "15552", "title": "Entrada y Salida Rápida"},
                {"id": "2741", "title": "Imprimir N"},
                {"id": "2742", "title": "Imprimir N al revés"},
                {"id": "11021", "title": "A+B - 7"},
                {"id": "11022", "title": "A+B - 8"},
                {"id": "2438", "title": "Imprimir estrellas - 1"},
                {"id": "2439", "title": "Imprimir estrellas - 2"},
                {"id": "10871", "title": "Menor que X"},
                {"id": "10952", "title": "A+B - 5"},
                {"id": "10951", "title": "A+B - 4"},
                {"id": "1110", "title": "Ciclo de sumas"},
                {"id": "10818", "title": "Mínimo y Máximo"},
                {"id": "2562", "title": "Encontrar máximo"},
                {"id": "2577", "title": "Contar números"},
                {"id": "3052", "title": "Residuos"},
                {"id": "1546", "title": "Promedio"},
                {"id": "8958", "title": "Puntaje OX"},
                {"id": "4344", "title": "¿Soy superior al promedio?"},
                {"id": "15596", "title": "Función suma"},
                {"id": "4673", "title": "Número constructor"},
                {"id": "1065", "title": "Número Han"},
                {"id": "11654", "title": "Valor ASCII"},
                {"id": "11720", "title": "Suma de dígitos"},
                {"id": "10809", "title": "Encontrar alfabeto"},
                {"id": "2675", "title": "Repetir string"},
                {"id": "1157", "title": "Estudio de palabras"},
                {"id": "1152", "title": "Contar palabras"},
                {"id": "2908", "title": "Sangsu"},
                {"id": "5622", "title": "Teléfono BAKA"},
                {"id": "2941", "title": "Alfabeto croata"},
                {"id": "1316", "title": "Palabras de grupo"},
                {"id": "1712", "title": "Punto de equilibrio"},
                {"id": "2839", "title": "Entrega de azúcar"},
                {"id": "2292", "title": "Panal de abeja"},
                {"id": "1193", "title": "Fracciones"},
            ]
        
        return sample_problems
    
    @staticmethod
    def get_additional_problems(start_position, count):
        """
        Generar problemas adicionales para expandir el ladder
        
        Args:
            start_position: Posición inicial para los nuevos problemas
            count: Cantidad de problemas a generar
            
        Returns:
            Lista de diccionarios con los problemas generados
        """
        import random
        
        # Obtener problemas de la base de datos en lugar de predefinirlos
        conn = sqlite3.connect('app.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Calcular un offset aleatorio para obtener problemas diferentes cada vez
        # Limitamos el offset para evitar quedarnos sin problemas
        cursor.execute("SELECT COUNT(*) FROM problems")
        total_problems = cursor.fetchone()[0]
        max_offset = max(0, total_problems - count - 1)
        random_offset = random.randint(0, max_offset) if max_offset > 0 else 0
        
        # Seleccionamos problemas aleatorios de la base de datos
        cursor.execute(
            """
            SELECT problem_id, problem_title, tier, level
            FROM problems
            ORDER BY tier, level
            LIMIT ? OFFSET ?
            """,
            (count, random_offset)
        )
        
        additional_problems = []
        for i, row in enumerate(cursor.fetchall()):
            position = start_position + i
            additional_problems.append({
                "id": row["problem_id"],
                "title": row["problem_title"],
                "position": position
            })
        
        conn.close()
        
        # Si no hay suficientes problemas en la base de datos, usamos problemas de ejemplo
        if len(additional_problems) < count:
            # Calcular cuántos problemas adicionales necesitamos
            remaining = count - len(additional_problems)
            
            # Crear problemas generados como respaldo
            operations = ["Suma", "Resta", "Multiplicación", "División", "Potencia", "Ordenamiento", 
                         "Búsqueda", "Grafos", "Árboles", "Dinámico", "Combinatoria"]
            
            start = len(additional_problems)
            for i in range(remaining):
                position = start_position + start + i
                problem_id = str(10000 + position)  # ID único basado en la posición
                operation = random.choice(operations)
                difficulty = "Nivel " + str((position // 10) + 1)
                title = f"{operation} - {difficulty}"
                
                additional_problems.append({
                    "id": problem_id,
                    "title": title,
                    "position": position
                })
        
        return additional_problems
    
    @staticmethod
    def add_problems_to_ladder(baekjoon_username, problems_data):
        """
        Añadir problemas adicionales al ladder
        
        Args:
            baekjoon_username: Nombre de usuario de Baekjoon
            problems_data: Lista de diccionarios con los problemas a añadir
        """
        conn = sqlite3.connect('app.db')
        cursor = conn.cursor()
        
        for problem in problems_data:
            cursor.execute(
                """
                INSERT INTO ladder_problems 
                (baekjoon_username, position, problem_id, problem_title, state) 
                VALUES (?, ?, ?, ?, ?)
                """,
                (baekjoon_username, problem['position'], problem['id'], problem['title'], 'hidden')
            )
        
        conn.commit()
        conn.close()
        return True
    
    @staticmethod
    def get_problem_info_from_solved_ac(problem_id):
        """
        Obtener información actualizada de un problema desde Solved.ac
        
        Args:
            problem_id: ID del problema en Baekjoon
        
        Returns:
            Diccionario con la información del problema o None si no se encuentra
        """
        problem_data = SolvedAcAPI.get_problem_by_id(problem_id)
        if not problem_data:
            return None
        
        # Actualizar la información en la base de datos
        conn = sqlite3.connect('app.db')
        cursor = conn.cursor()
        
        # Comprobar si el problema ya existe en la tabla 'problems'
        cursor.execute("SELECT 1 FROM problems WHERE problem_id = ?", (problem_id,))
        exists = cursor.fetchone()
        
        # Extraer datos relevantes
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
        else:
            # Insertar nuevo problema
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
        
        conn.commit()
        conn.close()
        
        return {
            "id": problem_id,
            "title": title,
            "tier": tier,
            "tags": tags_str,
            "level": level,
            "solved_count": solved_count,
            "accepted_user_count": accepted_user_count,
            "average_tries": average_tries
        }
    
    @staticmethod
    def get_problems_by_tier(tier_min, tier_max, limit=20):
        """
        Obtener problemas por rango de dificultad (tier)
        
        Args:
            tier_min: Tier mínimo (inclusive)
            tier_max: Tier máximo (inclusive)
            limit: Número máximo de problemas a devolver
            
        Returns:
            Lista de problemas que cumplen con el rango de dificultad
        """
        conn = sqlite3.connect('app.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute(
            """
            SELECT * FROM problems 
            WHERE tier BETWEEN ? AND ? 
            ORDER BY solved_count DESC 
            LIMIT ?
            """,
            (tier_min, tier_max, limit)
        )
        
        problems = []
        for row in cursor.fetchall():
            problems.append({
                "id": row["problem_id"],
                "title": row["problem_title"],
                "tier": row["tier"],
                "tags": row["tags"],
                "level": row["level"],
                "solved_count": row["solved_count"],
                "accepted_user_count": row["accepted_user_count"],
                "average_tries": row["average_tries"]
            })
        
        conn.close()
        return problems 