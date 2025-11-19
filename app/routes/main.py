from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.models.baekjoon_account import BaekjoonAccount
from app.models.ladder_problem import LadderProblem
from app.models.solved_problem import SolvedProblem
from app.models.user import User
from wtforms import StringField, SubmitField
from flask_wtf import FlaskForm
from wtforms.validators import DataRequired
from datetime import datetime, timedelta
import sqlite3
from app.utils.problem_recommender import ProblemRecommender
import psycopg2
from app.config import DB_TYPE, DATABASE_URL

# Función helper para obtener conexión según el tipo de BD
def get_db_connection():
    """Retorna una conexión a la base de datos según el tipo configurado"""
    if DB_TYPE == 'postgresql':
        return psycopg2.connect(DATABASE_URL)
    else:
        return sqlite3.connect('app.db')

main = Blueprint('main', __name__)

class BaekjoonAccountForm(FlaskForm):
    username = StringField('Nombre de usuario de Baekjoon', validators=[DataRequired()])
    submit = SubmitField('Añadir cuenta')

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    from app.utils.problem_recommender import ProblemRecommender
    
    form = BaekjoonAccountForm()
    
    # Obtener el valor de buchholz
    buchholz_value = ProblemRecommender.calculate_buchholz(current_user.id)
    
    # Obtener cuentas de Baekjoon del usuario actual
    accounts = BaekjoonAccount.get_accounts_by_user_id(current_user.id)
    
    # Obtener leaderboard de problemas resueltos
    leaderboard_positions = SolvedProblem.get_user_leaderboard_positions(current_user.id)
    
    if form.validate_on_submit():
        success, result = BaekjoonAccount.add_account(current_user.id, form.username.data)
        if success:
            flash('Cuenta de Baekjoon añadida correctamente', 'success')
            return redirect(url_for('main.dashboard'))
        else:
            flash(result, 'danger')
    
    return render_template(
        'dashboard.html', 
        form=form,
        accounts=accounts, 
        leaderboard_positions=leaderboard_positions,
        buchholz=buchholz_value
    )

@main.route('/account/delete/<int:account_id>', methods=['POST'])
@login_required
def delete_account(account_id):
    if BaekjoonAccount.delete_account(account_id, current_user.id):
        flash('Cuenta eliminada correctamente', 'success')
    else:
        flash('No se pudo eliminar la cuenta', 'danger')
    
    return redirect(url_for('main.dashboard'))

@main.route('/account/<int:account_id>/ladder', methods=['GET'])
@login_required
def view_ladder(account_id):
    # Import datetime here to fix the UnboundLocalError
    from datetime import datetime, timedelta
    
    # Verificar que la cuenta pertenece al usuario actual
    accounts = BaekjoonAccount.get_accounts_by_user_id(current_user.id)
    account = next((acc for acc in accounts if acc.id == account_id), None)
    
    if not account:
        flash('No tienes acceso a esta cuenta', 'danger')
        return redirect(url_for('main.dashboard'))
    
    # Obtener el nombre de usuario de Baekjoon
    baekjoon_username = account.baekjoon_username
    
    # Obtener los problemas del ladder usando el nombre de usuario de Baekjoon
    problems = LadderProblem.get_ladder_problems(baekjoon_username)
    
    # Si no hay problemas, inicializar el ladder
    if not problems:
        # Detectar automáticamente el grupo si solo hay uno disponible
        available_groups = LadderProblem.get_available_source_groups()
        source_group = available_groups[0] if len(available_groups) == 1 else None
        
        print(f"[DEBUG] Inicializando ladder con source_group: {source_group} (grupos disponibles: {available_groups})")
        
        sample_problems = LadderProblem.get_sample_problems(source_group=source_group)
        LadderProblem.initialize_ladder(baekjoon_username, sample_problems)
        problems = LadderProblem.get_ladder_problems(baekjoon_username)
    
    # Obtener los timestamps de revealed_at
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Recuperar los timestamps para todos los problemas
    if DB_TYPE == 'postgresql':
        cursor.execute(
            "SELECT id, revealed_at FROM ladder_problems WHERE baekjoon_username = %s", 
            (baekjoon_username,)
        )
    else:
        cursor.execute(
            "SELECT id, revealed_at FROM ladder_problems WHERE baekjoon_username = ?", 
            (baekjoon_username,)
        )
    
    revealed_timestamps = {}
    for row in cursor.fetchall():
        if row[1]:  # Si revealed_at no es NULL
            # En PostgreSQL es datetime, en SQLite es string
            if isinstance(row[1], str):
                revealed_timestamps[row[0]] = row[1]
            else:
                revealed_timestamps[row[0]] = row[1].isoformat()
        else:
            revealed_timestamps[row[0]] = None
        
        # Log all timestamps for debugging
        print(f"Problem ID: {row[0]}, revealed_at from DB: {revealed_timestamps[row[0]]}")
    
    conn.close()
    
    # Calcular el buchholz del usuario
    buchholz_value = ProblemRecommender.calculate_buchholz(current_user.id)
    
    # Añadir el revealed_at a cada problema
    for problem in problems:
        problem.revealed_at = revealed_timestamps.get(problem.id)
        
        # Log current problems for debugging
        if problem.state == 'current':
            print(f"CURRENT problem {problem.id}, revealed_at: {problem.revealed_at}")
            
            # Solo establecer revealed_at cuando el usuario interactúe explícitamente con un problema
            # No establecer automáticamente al cargar la página después de un reinicio de ladder
            # La interacción explícita se manejará en otra parte del código
            # Esta modificación permite que los problemas reiniciados comiencen sin timestamp
            # hasta que el usuario interactúe con ellos
    
    # Ordenar los problemas por posición para garantizar que se muestren en el orden correcto
    problems = sorted(problems, key=lambda p: p.position)
    
    # Solo mostrar problemas que NO estén ocultos
    visible_problems = [p for p in problems if p.state != 'hidden']
    
    # Si hay algún problema con revealed_at (ya abierto), agregar un placeholder gris
    has_revealed_problem = any(p.revealed_at for p in visible_problems if p.state == 'current')
    
    if has_revealed_problem:
        # Crear un problema placeholder para el siguiente
        class PlaceholderProblem:
            def __init__(self):
                self.id = None
                self.baekjoon_username = baekjoon_username
                self.position = max([p.position for p in problems], default=0) + 1
                self.problem_id = "?"
                self.problem_title = "Siguiente problema"
                self.state = 'hidden'
                self.tier = None
                self.tags = None
                self.level = None
                self.solved_count = 0
                self.accepted_user_count = 0
                self.average_tries = 0
                self.revealed_at = None
        
        visible_problems.append(PlaceholderProblem())
    
    # Organizar los problemas en filas para mostrarlos secuencialmente
    ladder_rows = []
    row_size = 8  # Número de problemas por fila
    
    # Si hay pocos problemas, mostrarlos todos en una fila
    if len(visible_problems) <= row_size:
        ladder_rows.append(visible_problems)
    else:
        # Dividir en filas de tamaño uniforme
        for i in range(0, len(visible_problems), row_size):
            row = visible_problems[i:i+row_size]
            ladder_rows.append(row)
    
    # Add a debugging variable to the template
    current_time = datetime.now()
    
    return render_template('ladder.html', 
                         account=account, 
                         ladder_rows=ladder_rows,
                         buchholz=buchholz_value,
                         debug_time=current_time.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3])

@main.route('/account/<int:account_id>/ladder/problem/<int:problem_id>/update', methods=['POST'])
@login_required
def update_problem_state(account_id, problem_id):
    # Verificar que la cuenta pertenece al usuario actual
    accounts = BaekjoonAccount.get_accounts_by_user_id(current_user.id)
    account = next((acc for acc in accounts if acc.id == account_id), None)
    
    if not account:
        flash('No tienes acceso a esta cuenta', 'danger')
        return redirect(url_for('main.dashboard'))
    
    # Obtener el nombre de usuario de Baekjoon
    baekjoon_username = account.baekjoon_username
    
    new_state = request.form.get('state')
    if new_state in ['solved', 'unsolved']:
        if LadderProblem.update_problem_state(problem_id, new_state):
            # Si el problema actual se resolvió
            if new_state == 'solved':
                # Guardar el problema resuelto para el usuario actual
                problems = LadderProblem.get_ladder_problems(baekjoon_username)
                current_problem = next((p for p in problems if p.id == problem_id), None)
                
                if current_problem:
                    # Obtener el rating actual antes del cambio
                    conn = sqlite3.connect('app.db')
                    cursor = conn.cursor()
                    cursor.execute("SELECT rating FROM users WHERE id = ?", (current_user.id,))
                    old_rating = cursor.fetchone()[0]
                    conn.close()
                    
                    # Guardar el problema resuelto y actualizar el rating
                    # También revelará automáticamente el siguiente problema recomendado
                    LadderProblem.save_solved_problem(
                        current_user.id,
                        current_problem.problem_id,
                        current_problem.problem_title,
                        current_problem.position
                    )
                    
                    # Obtener el nuevo rating después de la actualización
                    conn = sqlite3.connect('app.db')
                    cursor = conn.cursor()
                    cursor.execute("SELECT rating FROM users WHERE id = ?", (current_user.id,))
                    new_rating = cursor.fetchone()[0]
                    delta_rating = new_rating - old_rating
                    conn.close()
                    
                    # Mostrar mensaje con el cambio de rating
                    flash(f'¡Problema resuelto correctamente! Tu rating ha aumentado de {old_rating} a {new_rating} (+{delta_rating})', 'success')
                    flash('¡Felicitaciones! Puedes continuar con el siguiente problema cuando estés listo.', 'info')
                
                # Ya no necesitamos añadir más problemas aquí, ya que el recomendador añade uno nuevo cada vez
                # que se resuelve un problema

            else:
                flash(f'El estado del problema ha sido actualizado a {new_state}', 'success')
        else:
            flash('No se pudo actualizar el estado del problema', 'danger')
    
    return redirect(url_for('main.view_ladder', account_id=account_id))

@main.route('/account/<int:account_id>/ladder/reset', methods=['POST'])
@login_required
def reset_ladder(account_id):
    # Verificar que la cuenta pertenece al usuario actual
    accounts = BaekjoonAccount.get_accounts_by_user_id(current_user.id)
    account = next((acc for acc in accounts if acc.id == account_id), None)
    
    if not account:
        flash('No tienes acceso a esta cuenta', 'danger')
        return redirect(url_for('main.dashboard'))
    
    # Obtener el nombre de usuario de Baekjoon
    baekjoon_username = account.baekjoon_username
    
    # Borrar los problemas existentes y todos los datos relacionados
    LadderProblem.clear_ladder(baekjoon_username)
    
    # Detectar automáticamente el grupo si solo hay uno disponible
    available_groups = LadderProblem.get_available_source_groups()
    source_group = available_groups[0] if len(available_groups) == 1 else None
    
    print(f"[DEBUG] Reiniciando ladder con source_group: {source_group} (grupos disponibles: {available_groups})")
    
    # Inicializar el ladder con nuevos problemas
    sample_problems = LadderProblem.get_sample_problems(source_group=source_group)
    LadderProblem.initialize_ladder(baekjoon_username, sample_problems)
    
    # Limpiar cualquier dato de revealed_at almacenado en localStorage (manejado en la plantilla)
    flash('Ladder reiniciado correctamente', 'success')
    return redirect(url_for('main.view_ladder', account_id=account_id, reset='true'))

@main.route('/check_problem_solved/<username>/<problem_id>')
def check_problem_solved(username, problem_id):
    """
    Verifica si un usuario ha resuelto un problema específico en Baekjoon.
    Se puede proporcionar un intervalo de tiempo a través de parámetros GET:
    - days_ago: número de días hacia atrás para considerar (por defecto: 30)
    """
    try:
        # Obtener intervalo de tiempo de los parámetros (opcional)
        days_ago = request.args.get('days_ago', 30, type=int)
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days_ago)
        
        # Verificar si el problema fue resuelto
        success, message = BaekjoonAccount.check_problem_solved(
            username, problem_id, start_time, end_time
        )
        
        return jsonify({
            "success": success,
            "message": message,
            "username": username,
            "problem_id": problem_id,
            "interval": {
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "days_ago": days_ago
            }
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@main.route('/account/<int:account_id>/ladder/problem/<int:problem_id>/verify', methods=['POST'])
@login_required
def verify_problem_solved(account_id, problem_id):
    """Verifica automáticamente si un problema ha sido resuelto en Baekjoon y actualiza su estado"""
    try:
        # Verificar que la cuenta pertenece al usuario actual
        accounts = BaekjoonAccount.get_accounts_by_user_id(current_user.id)
        account = next((acc for acc in accounts if acc.id == account_id), None)
        
        if not account:
            flash('No tienes acceso a esta cuenta', 'danger')
            return redirect(url_for('main.dashboard'))
        
        # Obtener el nombre de usuario de Baekjoon
        baekjoon_username = account.baekjoon_username
        
        # Obtener todos los problemas del ladder para comprobar si falta poco para terminar
        problems = LadderProblem.get_ladder_problems(baekjoon_username)
        problem = next((p for p in problems if p.id == problem_id), None)
        
        if not problem:
            flash('Problema no encontrado', 'danger')
            return redirect(url_for('main.view_ladder', account_id=account_id))
        
        # Configurar el intervalo de tiempo
        end_time = datetime.now()
        
        # Usar el revealed_at del problema como inicio del intervalo si está disponible
        if problem.revealed_at:
            try:
                # Convertir la cadena revealed_at a objeto datetime
                revealed_at = datetime.fromisoformat(problem.revealed_at.replace('Z', '+00:00'))
                start_time = revealed_at
                
                # Verificar si ha pasado demasiado tiempo (más de 30 días)
                max_days = 30
                if (end_time - start_time).days > max_days:
                    # Si ha pasado demasiado tiempo, limitar el intervalo
                    start_time = end_time - timedelta(days=max_days)
                else:
                    # Todavía está dentro del intervalo de tiempo válido
                    success, message = BaekjoonAccount.check_problem_solved(
                        baekjoon_username, problem.problem_id, start_time, end_time
                    )
            except (ValueError, TypeError):
                # Si hay un error con el formato de la fecha, usar el intervalo predeterminado
                days_ago = request.form.get('days_ago', 30, type=int)
                start_time = end_time - timedelta(days=days_ago)
                success, message = BaekjoonAccount.check_problem_solved(
                    baekjoon_username, problem.problem_id, start_time, end_time
                )
        else:
            # Si no hay revealed_at, usar el intervalo predeterminado
            days_ago = request.form.get('days_ago', 30, type=int)
            start_time = end_time - timedelta(days=days_ago)
            success, message = BaekjoonAccount.check_problem_solved(
                baekjoon_username, problem.problem_id, start_time, end_time
            )
        
        if success:
            # Si fue resuelto, actualizar el estado y aplicar todo lo necesario (ratings, etc.)
            # Obtener el rating actual antes del cambio
            conn = get_db_connection()
            cursor = conn.cursor()
            
            if DB_TYPE == 'postgresql':
                # Llamar a la función de PostgreSQL que actualiza todo
                cursor.execute('SELECT verify_solved_problem(%s, %s)', (problem_id, current_user.id))
                result = cursor.fetchone()[0]
            else:
                # Para SQLite, actualizar manualmente
                LadderProblem.save_solved_problem(
                    current_user.id,
                    problem.problem_id,
                    problem.problem_title,
                    problem.position
                )
                result = True
            
            conn.commit()
            conn.close()
            
            if result:
                # Obtener el rating actual
                conn = get_db_connection()
                cursor = conn.cursor()
                
                if DB_TYPE == 'postgresql':
                    cursor.execute('SELECT rating FROM users WHERE id = %s', (current_user.id,))
                else:
                    cursor.execute('SELECT rating FROM users WHERE id = ?', (current_user.id,))
                new_rating = cursor.fetchone()[0]
                conn.close()
                
                # Mostrar mensaje con el cambio de rating (asumimos que ya cambió)
                from app.utils.constants import Constants
                problem_level = problem.level or Constants.DEFAULT_USER_RATING
                expected_increase = max(25, min(200, int(problem_level * 0.05)))
                old_rating = new_rating - expected_increase
                
                flash(f'¡Problema verificado como resuelto! Tu rating ha aumentado de {old_rating} a {new_rating} (+{expected_increase})', 'success')
                flash('¡Felicitaciones! Puedes continuar con el siguiente problema cuando estés listo.', 'info')
            else:
                flash('No se pudo actualizar el estado del problema', 'danger')
        else:
            flash(f'Verificación fallida: {message}', 'warning')
        
        return redirect(url_for('main.view_ladder', account_id=account_id))
    
    except Exception as e:
        # Capturar cualquier error y mostrar un mensaje
        flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('main.view_ladder', account_id=account_id))

@main.route('/solved-problems')
@login_required
def solved_problems():
    """Mostrar los problemas resueltos por el usuario con sus posiciones en el leaderboard"""
    from app.utils.problem_recommender import ProblemRecommender
    
    user_id = current_user.id
    
    # Obtener problemas resueltos
    from app.db import Database
    from app.config import DB_TYPE
    
    try:
        if DB_TYPE == 'postgresql':
            # Usar la función de PostgreSQL para obtener problemas resueltos
            query = "SELECT * FROM get_solved_problems(%s)"
        else:
            # Para SQLite, obtener directamente de la tabla
            query = """
                SELECT id, problem_id, problem_title, position, solved_at, 0 as level, 0 as rating_change
                FROM solved_problems
                WHERE user_id = ?
                ORDER BY solved_at DESC
            """
        
        results = Database.execute_query(query, (user_id,))
        
        # Convertir los resultados a diccionarios para facilitar el acceso en la plantilla
        solved_problems = []
        for problem in results:
            solved_problems.append({
                'id': problem[0],
                'problem_id': problem[1],
                'problem_title': problem[2],
                'position': problem[3],
                'solved_at': problem[4],
                'level': problem[5] if len(problem) > 5 else 0,
                'rating_change': problem[6] if len(problem) > 6 else 0
            })
    except Exception as e:
        print(f"Error al obtener problemas resueltos: {str(e)}")
        import traceback
        traceback.print_exc()
        solved_problems = []  # Si hay error, devolver lista vacía
    
    # Obtener el valor de buchholz
    buchholz_value = ProblemRecommender.calculate_buchholz(user_id)
    
    return render_template(
        'solved_problems.html', 
        solved_problems=solved_problems,
        buchholz=buchholz_value
    )

@main.route('/problem/<int:problem_id>/mark_time_expired', methods=['POST'])
@login_required
def mark_time_expired(problem_id):
    """
    Marca un problema como 'unsolved' cuando se agota el tiempo
    """
    try:
        # Obtener información del problema
        problem = LadderProblem.get_problem_by_id(problem_id)
        
        if not problem:
            return jsonify({
                "success": False,
                "message": "Problema no encontrado"
            }), 404
        
        # Verificar que la cuenta pertenece al usuario actual
        accounts = BaekjoonAccount.get_accounts_by_user_id(current_user.id)
        account = next((acc for acc in accounts if acc.baekjoon_username == problem.baekjoon_username), None)
        
        if not account:
            return jsonify({
                "success": False,
                "message": "No tienes acceso a esta cuenta"
            }), 403
        
        # Obtener el rating actual antes de actualizar
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if DB_TYPE == 'postgresql':
            cursor.execute('SELECT rating FROM users WHERE id = %s', (current_user.id,))
        else:
            cursor.execute('SELECT rating FROM users WHERE id = ?', (current_user.id,))
        old_rating = cursor.fetchone()[0]
        
        conn.close()
        
        # Asegurar que problem.tier es un número
        try:
            problem_tier = int(problem.tier) if problem.tier is not None else 15
        except (ValueError, TypeError):
            problem_tier = 15  # tier por defecto
        
        print(f"[DEBUG] Time expired for problem {problem_id}: old_rating={old_rating}, problem_tier={problem_tier}")
        
        # Calcular la pérdida de rating basada en el tier del problema
        from app.utils.rating_calculator import RatingCalculator
        penalty = RatingCalculator.calculate_rating_loss(old_rating, problem_tier)
        
        print(f"[DEBUG] Calculated penalty: {penalty}")
        
        User.update_rating(current_user.id, penalty)
        
        print(f"[DEBUG] Applied penalty of {penalty}, updated rating")
        
        # Revelar el siguiente problema ANTES de marcar como unsolved
        from app.utils.problem_recommender import ProblemRecommender
        next_problem_id = ProblemRecommender.reveal_next_problem(current_user.id, problem.baekjoon_username)
        
        print(f"[DEBUG] Revealed next problem: next_problem_id={next_problem_id}")
        
        # Actualizar el estado a 'unsolved'
        LadderProblem.update_problem_state(problem_id, 'unsolved')
        
        print(f"[DEBUG] Updated problem state to unsolved")
        
        # Obtener el nuevo rating
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if DB_TYPE == 'postgresql':
            cursor.execute('SELECT rating FROM users WHERE id = %s', (current_user.id,))
        else:
            cursor.execute('SELECT rating FROM users WHERE id = ?', (current_user.id,))
        new_rating = cursor.fetchone()[0]
        
        conn.close()
        
        return jsonify({
            "success": True,
            "message": f"Tiempo agotado. Rating: {old_rating} → {new_rating} ({penalty})",
            "rating_change": penalty,
            "old_rating": old_rating,
            "new_rating": new_rating,
            "next_problem_revealed": next_problem_id is not None
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

@main.route('/set_revealed_at/<int:problem_id>', methods=['POST'])
@login_required
def set_revealed_at(problem_id):
    """
    Establece la marca de tiempo revealed_at para un problema específico cuando 
    el usuario interactúa con él por primera vez
    """
    try:
        # Obtener información del problema
        problem = LadderProblem.get_problem_by_id(problem_id)
        
        if not problem:
            return jsonify({
                "success": False,
                "message": "Problema no encontrado"
            }), 404
        
        # Verificar que la cuenta pertenece al usuario actual
        accounts = BaekjoonAccount.get_accounts_by_user_id(current_user.id)
        account = next((acc for acc in accounts if acc.baekjoon_username == problem.baekjoon_username), None)
        
        if not account:
            return jsonify({
                "success": False,
                "message": "No tienes acceso a esta cuenta"
            }), 403
        
        # Establecer revealed_at
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if DB_TYPE == 'postgresql':
            # Llamar a la función de PostgreSQL para establecer revealed_at
            cursor.execute("SELECT set_problem_revealed_at(%s)", (problem_id,))
            timestamp = cursor.fetchone()[0]
            timestamp_str = timestamp.isoformat()
        else:
            # Para SQLite, actualizar directamente
            from datetime import datetime
            timestamp = datetime.now()
            timestamp_str = timestamp.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3]
            cursor.execute(
                "UPDATE ladder_problems SET revealed_at = ? WHERE id = ?",
                (timestamp_str, problem_id)
            )
        
        conn.commit()
        conn.close()
        
        return jsonify({
            "success": True,
            "revealed_at": timestamp_str
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500 