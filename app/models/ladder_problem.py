import sqlite3
import requests
from app.models.solved_problem import SolvedProblem
from app.utils.solved_ac_api import SolvedAcAPI
from app.utils.rating_calculator import RatingCalculator
from app.models.user import User
from app.utils.problem_recommender import ProblemRecommender
import psycopg2
from app.config import DB_TYPE, DATABASE_URL

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
    def get_database_connection():
        """Obtener una conexión a la base de datos PostgreSQL"""
        pg_url = DATABASE_URL
        if 'postgresql:' not in pg_url:
            pg_url = "postgresql://ladder_db_user:6FCOPInpMsKIazgN7WbdXd1dzsUwZVmv@dpg-d01m3rruibrs73aurmt0-a.virginia-postgres.render.com/ladder_db"
        return psycopg2.connect(pg_url)
    
    @staticmethod
    def get_ladder_problems(baekjoon_username):
        """Obtener todos los problemas del ladder para un nombre de usuario de Baekjoon"""
        conn = LadderProblem.get_database_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            """
            SELECT lp.*, p.tier, p.tags, p.level, p.solved_count, 
                   p.accepted_user_count, p.average_tries
            FROM ladder_problems lp
            LEFT JOIN problems p ON lp.problem_id = p.problem_id
            WHERE lp.baekjoon_username = %s 
            ORDER BY lp.position ASC
            """,
            (baekjoon_username,)
        )
        
        problems = []
        for row in cursor.fetchall():
            # Obtener los valores por posición
            id = row[0]
            username = row[1]
            position = row[2]
            problem_id = row[3]
            problem_title = row[4]
            state = row[5]
            revealed_at = row[6] if len(row) > 6 else None
            
            # Datos adicionales de la tabla problems (si están disponibles)
            tier = row[7] if len(row) > 7 and row[7] is not None else None
            tags = row[8] if len(row) > 8 and row[8] is not None else None
            level = row[9] if len(row) > 9 and row[9] is not None else None
            solved_count = row[10] if len(row) > 10 and row[10] is not None else 0
            accepted_user_count = row[11] if len(row) > 11 and row[11] is not None else 0
            average_tries = row[12] if len(row) > 12 and row[12] is not None else 0.0
            
            problems.append(LadderProblem(
                id=id,
                baekjoon_username=username,
                position=position,
                problem_id=problem_id,
                problem_title=problem_title,
                state=state,
                tier=tier,
                tags=tags,
                level=level,
                solved_count=solved_count,
                accepted_user_count=accepted_user_count,
                average_tries=average_tries,
                revealed_at=revealed_at
            ))
        
        conn.close()
        return problems
    
    @staticmethod
    def get_problem_by_id(ladder_problem_id):
        """Obtener un problema específico del ladder por su ID"""
        conn = LadderProblem.get_database_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            """
            SELECT lp.*, p.tier, p.tags, p.level, p.solved_count, 
                   p.accepted_user_count, p.average_tries
            FROM ladder_problems lp
            LEFT JOIN problems p ON lp.problem_id = p.problem_id
            WHERE lp.id = %s
            """,
            (ladder_problem_id,)
        )
        
        row = cursor.fetchone()
        if not row:
            conn.close()
            return None
        
        # Obtener los valores por posición
        id = row[0]
        username = row[1]
        position = row[2]
        problem_id = row[3]
        problem_title = row[4]
        state = row[5]
        revealed_at = row[6] if len(row) > 6 else None
        
        # Datos adicionales de la tabla problems (si están disponibles)
        tier = row[7] if len(row) > 7 and row[7] is not None else None
        tags = row[8] if len(row) > 8 and row[8] is not None else None
        level = row[9] if len(row) > 9 and row[9] is not None else None
        solved_count = row[10] if len(row) > 10 and row[10] is not None else 0
        accepted_user_count = row[11] if len(row) > 11 and row[11] is not None else 0
        average_tries = row[12] if len(row) > 12 and row[12] is not None else 0.0
        
        problem = LadderProblem(
            id=id,
            baekjoon_username=username,
            position=position,
            problem_id=problem_id,
            problem_title=problem_title,
            state=state,
            tier=tier,
            tags=tags,
            level=level,
            solved_count=solved_count,
            accepted_user_count=accepted_user_count,
            average_tries=average_tries,
            revealed_at=revealed_at
        )
        
        conn.close()
        return problem
    
    @staticmethod
    def initialize_ladder(baekjoon_username, problems_data):
        """Inicializar el ladder con problemas para un nombre de usuario de Baekjoon"""
        import psycopg2
        DATABASE_URL = "postgresql://ladder_db_user:6FCOPInpMsKIazgN7WbdXd1dzsUwZVmv@dpg-d01m3rruibrs73aurmt0-a.virginia-postgres.render.com/ladder_db"
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # Primero obtener el user_id del baekjoon_username
        cursor.execute(
            "SELECT user_id FROM baekjoon_accounts WHERE baekjoon_username = %s LIMIT 1",
            (baekjoon_username,)
        )
        
        account_data = cursor.fetchone()
        user_id = account_data[0] if account_data else None
        
        # Inicializar el primer problema como 'hidden' en lugar de 'current'
        if problems_data and len(problems_data) > 0:
            first_problem = problems_data[0]
            cursor.execute(
                """
                INSERT INTO ladder_problems 
                (baekjoon_username, position, problem_id, problem_title, state) 
                VALUES (%s, %s, %s, %s, %s)
                """,
                (baekjoon_username, 1, first_problem['id'], first_problem['title'], 'hidden')
            )
            print(f"Inicializando ladder para {baekjoon_username}: añadido problema {first_problem['id']} ({first_problem['title']}) como 'hidden'")
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
        
        if not problem_data:
            conn.close()
            return False
        
        baekjoon_username = problem_data['baekjoon_username']
        
        # Si el estado nuevo es 'solved', asegurarnos de que solo haya un problema 'current'
        if new_state == 'solved':
            # Primero actualizar este problema a 'solved'
            cursor.execute(
                "UPDATE ladder_problems SET state = ? WHERE id = ?",
                (new_state, problem_id)
            )
            
            # El sistema de recomendación se encargará de añadir el siguiente problema como 'current'
        elif new_state == 'current':
            # Si vamos a marcar un problema como 'current', primero asegurarnos
            # de que no haya otros problemas 'current' para este usuario
            cursor.execute(
                """
                UPDATE ladder_problems 
                SET state = 'hidden' 
                WHERE baekjoon_username = ? AND state = 'current' AND id != ?
                """,
                (baekjoon_username, problem_id)
            )
            
            # Ahora actualizar el revealed_at con la hora actual
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
            # Para otros estados, simplemente actualizar
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
        return True
    
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
        
        # Actualizar el estado de este problema a 'solved' en ladder_problems
        cursor.execute(
            """
            UPDATE ladder_problems 
            SET state = 'solved' 
            WHERE problem_id = ? AND baekjoon_username IN (
                SELECT baekjoon_username FROM baekjoon_accounts WHERE user_id = ?
            )
            """,
            (problem_id, user_id)
        )
        
        conn.commit()
        conn.close()
        
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
        import psycopg2
        DATABASE_URL = "postgresql://ladder_db_user:6FCOPInpMsKIazgN7WbdXd1dzsUwZVmv@dpg-d01m3rruibrs73aurmt0-a.virginia-postgres.render.com/ladder_db"
        try:
            conn = psycopg2.connect(DATABASE_URL)
            cursor = conn.cursor()
            
            # Eliminar todos los problemas del ladder
            cursor.execute(
                "DELETE FROM ladder_problems WHERE baekjoon_username = %s",
                (baekjoon_username,)
            )
            
            deleted_count = cursor.rowcount
            print(f"Se eliminaron {deleted_count} problemas del ladder para el usuario {baekjoon_username}")
            
            conn.commit()
            conn.close()
            return deleted_count > 0
        except Exception as e:
            print(f"Error al limpiar el ladder: {str(e)}")
            return False
    
    @staticmethod
    def get_sample_problems():
        """Obtener una lista de problemas de ejemplo para inicializar el ladder"""
        # Obtener problemas de la base de datos
        import psycopg2
        DATABASE_URL = "postgresql://ladder_db_user:6FCOPInpMsKIazgN7WbdXd1dzsUwZVmv@dpg-d01m3rruibrs73aurmt0-a.virginia-postgres.render.com/ladder_db"
        try:
            conn = psycopg2.connect(DATABASE_URL)
            cursor = conn.cursor()
            
            # Seleccionar UN problema aleatorio
            cursor.execute(
                """
                SELECT problem_id, problem_title 
                FROM problems 
                ORDER BY RANDOM()
                LIMIT 1
                """
            )
            
            problem = cursor.fetchone()
            
            # Si encontramos un problema, devolverlo como único elemento de la lista
            if problem:
                sample_problems = [{
                    "id": problem[0],
                    "title": problem[1]
                }]
                print(f"Se seleccionó el problema aleatorio {problem[0]}: {problem[1]}")
            else:
                # Si no hay problemas, seleccionar un problema específico
                sample_problems = [{"id": "21065", "title": "Friendship Circles"}]
                print("No se encontraron problemas en la BD, usando el problema predeterminado 21065")
            
            conn.close()
            return sample_problems
        except Exception as e:
            print(f"Error al obtener problema de muestra: {str(e)}")
            # Problema de respaldo en caso de error
            return [{"id": "21065", "title": "Friendship Circles"}]
    
    @staticmethod
    def get_additional_problems(count):
        """
        Generar problemas adicionales para expandir el ladder
        
        Args:
            count: Cantidad de problemas a generar
            
        Returns:
            Lista de diccionarios con los problemas generados (sin posiciones)
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
        for row in cursor.fetchall():
            additional_problems.append({
                "id": row["problem_id"],
                "title": row["problem_title"]
            })
        
        conn.close()
        
        # Si no hay suficientes problemas en la base de datos, usamos problemas de ejemplo
        if len(additional_problems) < count:
            # Calcular cuántos problemas adicionales necesitamos
            remaining = count - len(additional_problems)
            
            # Crear problemas generados como respaldo
            operations = ["Suma", "Resta", "Multiplicación", "División", "Potencia", "Ordenamiento", 
                         "Búsqueda", "Grafos", "Árboles", "Dinámico", "Combinatoria"]
            
            for i in range(remaining):
                problem_id = str(10000 + len(additional_problems) + i)  # ID único
                operation = random.choice(operations)
                difficulty = "Nivel " + str((i // 5) + 1)
                title = f"{operation} - {difficulty}"
                
                additional_problems.append({
                    "id": problem_id,
                    "title": title
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
        
        # Primero obtener la posición máxima actual
        cursor.execute(
            """
            SELECT MAX(position) 
            FROM ladder_problems
            WHERE baekjoon_username = ?
            """,
            (baekjoon_username,)
        )
        
        result = cursor.fetchone()
        max_position = result[0] if result[0] is not None else 0
        
        # Obtener los IDs de problemas que ya están en el ladder
        cursor.execute(
            """
            SELECT problem_id 
            FROM ladder_problems
            WHERE baekjoon_username = ?
            """,
            (baekjoon_username,)
        )
        
        existing_problem_ids = [row[0] for row in cursor.fetchall()]
        
        # Añadir problemas asegurándose de que no haya duplicados de IDs o posiciones
        for i, problem in enumerate(problems_data):
            # Verificar que el problema no esté ya en el ladder
            if problem['id'] in existing_problem_ids:
                continue
                
            # Asignar la siguiente posición disponible
            next_position = max_position + i + 1
            
            cursor.execute(
                """
                INSERT INTO ladder_problems 
                (baekjoon_username, position, problem_id, problem_title, state) 
                VALUES (?, ?, ?, ?, ?)
                """,
                (baekjoon_username, next_position, problem['id'], problem['title'], 'hidden')
            )
            
            # Añadir a la lista de problemas existentes para evitar duplicados
            existing_problem_ids.append(problem['id'])
        
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