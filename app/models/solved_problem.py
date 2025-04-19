import sqlite3
from datetime import datetime

class SolvedProblem:
    def __init__(self, id, user_id, problem_id, problem_title, position, solved_at):
        self.id = id
        self.user_id = user_id
        self.problem_id = problem_id
        self.problem_title = problem_title
        self.position = position
        self.solved_at = solved_at
    
    @staticmethod
    def get_solved_problems(user_id):
        """Obtener todos los problemas resueltos por un usuario"""
        conn = sqlite3.connect('app.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT * FROM solved_problems WHERE user_id = ? ORDER BY solved_at DESC",
            (user_id,)
        )
        
        solved_problems = []
        for problem_data in cursor.fetchall():
            solved_problems.append(SolvedProblem(
                id=problem_data['id'],
                user_id=problem_data['user_id'],
                problem_id=problem_data['problem_id'],
                problem_title=problem_data['problem_title'],
                position=problem_data['position'],
                solved_at=problem_data['solved_at']
            ))
        
        conn.close()
        return solved_problems
    
    @staticmethod
    def save_solved_problem(user_id, problem_id, problem_title, position):
        """Guardar un problema resuelto por un usuario con su posición en el leaderboard"""
        conn = sqlite3.connect('app.db')
        cursor = conn.cursor()
        
        # Verificar si ya existe este problema resuelto para el usuario
        cursor.execute(
            "SELECT id FROM solved_problems WHERE user_id = ? AND problem_id = ?",
            (user_id, problem_id)
        )
        
        existing = cursor.fetchone()
        
        if existing:
            # Actualizar la posición si ya existe
            cursor.execute(
                "UPDATE solved_problems SET position = ?, solved_at = CURRENT_TIMESTAMP WHERE id = ?",
                (position, existing[0])
            )
        else:
            # Insertar nuevo registro
            cursor.execute(
                """
                INSERT INTO solved_problems 
                (user_id, problem_id, problem_title, position) 
                VALUES (?, ?, ?, ?)
                """,
                (user_id, problem_id, problem_title, position)
            )
        
        conn.commit()
        conn.close()
        return True
    
    @staticmethod
    def delete_solved_problem(problem_id, user_id):
        """Eliminar un problema resuelto"""
        conn = sqlite3.connect('app.db')
        cursor = conn.cursor()
        
        cursor.execute(
            "DELETE FROM solved_problems WHERE problem_id = ? AND user_id = ?",
            (problem_id, user_id)
        )
        
        conn.commit()
        conn.close()
        return cursor.rowcount > 0
    
    @staticmethod
    def get_user_leaderboard_positions(user_id):
        """Obtener todas las posiciones de leaderboard del usuario"""
        conn = sqlite3.connect('app.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT problem_id, problem_title, position FROM solved_problems WHERE user_id = ? ORDER BY position ASC",
            (user_id,)
        )
        
        positions = cursor.fetchall()
        conn.close()
        return positions 