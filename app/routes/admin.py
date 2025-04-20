from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, render_template_string
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, IntegerField
from wtforms.validators import DataRequired, Email, NumberRange
from app.models.user import User
from app.models.ladder_problem import LadderProblem
import os
import psycopg2
from app.config import DATABASE_URL

admin = Blueprint('admin', __name__)

class WhitelistForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    notes = TextAreaField('Notas')
    submit = SubmitField('Añadir a la Whitelist')

class ProblemRangeForm(FlaskForm):
    start_id = IntegerField('ID Inicio', validators=[DataRequired(), NumberRange(min=1000)])
    end_id = IntegerField('ID Fin', validators=[DataRequired(), NumberRange(min=1000)])
    submit = SubmitField('Agregar Rango')

class SingleProblemForm(FlaskForm):
    problem_id = IntegerField('ID del Problema', validators=[DataRequired(), NumberRange(min=1000)])
    submit = SubmitField('Agregar Problema')

@admin.route('/')
@login_required
def admin_index():
    # Verificar si el usuario es admin (asumimos que el admin tiene ID 1)
    if current_user.id != 1:
        flash('Acceso denegado. Solo administradores pueden acceder a esta sección.', 'danger')
        return redirect(url_for('main.index'))
    
    # Lista de emails en la whitelist
    whitelist = User.get_whitelist()
    
    return render_template('admin/index.html', whitelist=whitelist)

@admin.route('/whitelist/add', methods=['POST'])
@login_required
def add_to_whitelist():
    # Verificar si el usuario es admin (asumimos que el admin tiene ID 1)
    if current_user.id != 1:
        flash('Acceso denegado. Solo administradores pueden añadir emails a la whitelist.', 'danger')
        return redirect(url_for('admin.admin_index'))
    
    email = request.form.get('email')
    notes = request.form.get('notes', '')
    
    if not email:
        flash('El email es requerido.', 'danger')
        return redirect(url_for('admin.admin_index'))
    
    # Añadir email a la whitelist
    if User.add_email_to_whitelist(email, notes):
        flash(f'Email {email} añadido a la whitelist.', 'success')
    else:
        flash(f'El email {email} ya existe en la whitelist.', 'warning')
    
    return redirect(url_for('admin.admin_index'))

@admin.route('/whitelist/remove/<email>', methods=['POST'])
@login_required
def remove_from_whitelist(email):
    # Verificar si el usuario es admin
    if current_user.id != 1:
        flash('Acceso denegado. Solo administradores pueden eliminar emails de la whitelist.', 'danger')
        return redirect(url_for('admin.admin_index'))
    
    # Eliminar email de la whitelist
    if User.remove_email_from_whitelist(email):
        flash(f'Email {email} eliminado de la whitelist.', 'success')
    else:
        flash(f'Error al eliminar {email} de la whitelist.', 'danger')
    
    return redirect(url_for('admin.admin_index'))

# ----------- NUEVA SECCIÓN PARA GESTIÓN DE PROBLEMAS -------------

@admin.route('/setup')
@login_required
def setup_page():
    # Verificar si el usuario es admin
    if current_user.id != 1:
        flash('Acceso denegado. Solo administradores pueden acceder a esta sección.', 'danger')
        return redirect(url_for('main.index'))
    
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Configuración de Problemas</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
            .button { background-color: #4CAF50; color: white; padding: 10px 15px; border: none; cursor: pointer; margin: 5px; }
            .warning { background-color: #f44336; }
            .success { color: green; font-weight: bold; }
            .error { color: red; font-weight: bold; }
        </style>
    </head>
    <body>
        <h1>Configuración de Ladder App</h1>
        <a href="{{ url_for('admin.admin_index') }}">← Volver al Panel Admin</a>
        
        <h2>Acciones de administración</h2>
        <form action="{{ url_for('admin.setup_baekjoon') }}" method="post">
            <button class="button">Configurar cuenta Baekjoon para Admin</button>
        </form>
        
        <form action="{{ url_for('admin.add_example_problems') }}" method="post">
            <button class="button">Añadir problemas de ejemplo</button>
        </form>
        
        <form action="{{ url_for('admin.reset_problems') }}" method="post" onsubmit="return confirm('¿Estás seguro? Esta acción eliminará TODOS los problemas.')">
            <button class="button warning">Reiniciar todos los problemas</button>
        </form>
        
        <p>Nota: Todas las operaciones se realizan para el usuario administrador (ID: 1)</p>
    </body>
    </html>
    ''')

@admin.route('/setup/baekjoon', methods=['POST'])
@login_required
def setup_baekjoon():
    # Verificar si el usuario es admin
    if current_user.id != 1:
        flash('Acceso denegado.', 'danger')
        return redirect(url_for('admin.setup_page'))
    
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # Configurar cuenta de Baekjoon para el admin
        cursor.execute("""
        INSERT INTO baekjoon_accounts (user_id, baekjoon_username) 
        VALUES (%s, 'admin_baekjoon') 
        ON CONFLICT (user_id, baekjoon_username) DO NOTHING
        """, (current_user.id,))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        flash('Cuenta Baekjoon configurada correctamente.', 'success')
        
    except Exception as e:
        flash(f'Error: {str(e)}', 'danger')
    
    return redirect(url_for('admin.setup_page'))

@admin.route('/setup/problems', methods=['POST'])
@login_required
def add_example_problems():
    # Verificar si el usuario es admin
    if current_user.id != 1:
        flash('Acceso denegado.', 'danger')
        return redirect(url_for('admin.setup_page'))
    
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # Verificar si existe la cuenta baekjoon para admin
        cursor.execute("SELECT id FROM baekjoon_accounts WHERE user_id = %s", (current_user.id,))
        account = cursor.fetchone()
        
        if not account:
            flash('Error: Primero debes configurar una cuenta Baekjoon.', 'danger')
            return redirect(url_for('admin.setup_page'))
            
        # Limpiar problemas existentes para evitar conflictos
        cursor.execute("DELETE FROM ladder_problems WHERE baekjoon_username = 'admin_baekjoon'")
        
        # Crear problemas de ejemplo secuenciales y con estado apropiado
        problem_count = 0
        for i in range(1, 51):  # Crear 50 problemas para tener suficientes
            # Solo el primer problema es visible, el resto están ocultos
            state = 'visible' if i == 1 else 'hidden'
            
            cursor.execute("""
            INSERT INTO ladder_problems (baekjoon_username, position, problem_id, problem_title, state)
            VALUES ('admin_baekjoon', %s, %s, %s, %s)
            """, (i, f"{1000+i}", f"Ejemplo #{i} - Dificultad {i*100}", state))
            problem_count += 1
        
        conn.commit()
        cursor.close()
        conn.close()
        
        flash(f'Se han configurado {problem_count} problemas correctamente. Solo el primero está visible, los demás se revelarán secuencialmente al resolver problemas.', 'success')
        
    except Exception as e:
        flash(f'Error: {str(e)}', 'danger')
    
    return redirect(url_for('admin.setup_page'))

@admin.route('/setup/reset', methods=['POST'])
@login_required
def reset_problems():
    # Verificar si el usuario es admin
    if current_user.id != 1:
        flash('Acceso denegado.', 'danger')
        return redirect(url_for('admin.setup_page'))
    
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # Eliminar todos los problemas del ladder
        cursor.execute("DELETE FROM ladder_problems")
        count = cursor.rowcount
        
        conn.commit()
        cursor.close()
        conn.close()
        
        flash(f'Se han eliminado {count} problemas del ladder.', 'success')
        
    except Exception as e:
        flash(f'Error: {str(e)}', 'danger')
    
    return redirect(url_for('admin.setup_page'))

# ----------- PROBLEMA MANAGEMENT SECTION -------------

@admin.route('/problems')
@login_required
def problems_management():
    # Verificar si el usuario es admin
    if current_user.id != 1:
        flash('Acceso denegado. Solo administradores pueden acceder a esta sección.', 'danger')
        return redirect(url_for('main.index'))
    
    # Preparar los formularios
    range_form = ProblemRangeForm()
    single_form = SingleProblemForm()
    
    # Obtener los últimos 20 problemas para mostrar en la página
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT problem_id, problem_title, tier, tags, solved_count
            FROM problems
            ORDER BY id DESC
            LIMIT 20
        """)
        
        recent_problems = [
            {
                'id': row[0],
                'title': row[1],
                'tier': row[2],
                'tags': row[3],
                'solved_count': row[4]
            }
            for row in cursor.fetchall()
        ]
        
        # Contar el total de problemas
        cursor.execute("SELECT COUNT(*) FROM problems")
        total_problems = cursor.fetchone()[0]
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        recent_problems = []
        total_problems = 0
        flash(f'Error al obtener problemas: {str(e)}', 'danger')
    
    return render_template('admin/problems.html', 
                          range_form=range_form, 
                          single_form=single_form,
                          recent_problems=recent_problems,
                          total_problems=total_problems)

@admin.route('/problems/add-single', methods=['POST'])
@login_required
def add_single_problem():
    # Verificar si el usuario es admin
    if current_user.id != 1:
        flash('Acceso denegado.', 'danger')
        return redirect(url_for('admin.problems_management'))
    
    form = SingleProblemForm()
    
    if form.validate_on_submit():
        problem_id = str(form.problem_id.data)
        
        try:
            # Obtener información del problema desde Solved.ac
            problem_info = LadderProblem.get_problem_info_from_solved_ac(problem_id)
            
            if problem_info:
                flash(f'Problema "{problem_info["title"]}" agregado correctamente.', 'success')
            else:
                flash(f'No se pudo obtener información del problema {problem_id}.', 'warning')
        
        except Exception as e:
            flash(f'Error al agregar el problema: {str(e)}', 'danger')
    
    return redirect(url_for('admin.problems_management'))

@admin.route('/problems/add-range', methods=['POST'])
@login_required
def add_problem_range():
    # Verificar si el usuario es admin
    if current_user.id != 1:
        flash('Acceso denegado.', 'danger')
        return redirect(url_for('admin.problems_management'))
    
    form = ProblemRangeForm()
    
    if form.validate_on_submit():
        start_id = form.start_id.data
        end_id = form.end_id.data
        
        if start_id > end_id:
            flash('El ID de inicio debe ser menor o igual al ID final.', 'danger')
            return redirect(url_for('admin.problems_management'))
        
        if end_id - start_id > 100:
            flash('El rango no puede contener más de 100 problemas.', 'danger')
            return redirect(url_for('admin.problems_management'))
        
        try:
            added_count = 0
            for problem_id in range(start_id, end_id + 1):
                problem_info = LadderProblem.get_problem_info_from_solved_ac(str(problem_id))
                if problem_info:
                    added_count += 1
            
            flash(f'Se agregaron {added_count} problemas correctamente.', 'success')
        
        except Exception as e:
            flash(f'Error al agregar el rango de problemas: {str(e)}', 'danger')
    
    return redirect(url_for('admin.problems_management'))

@admin.route('/problems/list')
@login_required
def list_all_problems():
    # Verificar si el usuario es admin
    if current_user.id != 1:
        flash('Acceso denegado. Solo administradores pueden acceder a esta sección.', 'danger')
        return redirect(url_for('main.index'))
    
    # Parámetros de paginación
    page = request.args.get('page', 1, type=int)
    per_page = 50
    offset = (page - 1) * per_page
    
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # Obtener el total de problemas para la paginación
        cursor.execute("SELECT COUNT(*) FROM problems")
        total = cursor.fetchone()[0]
        
        # Obtener los problemas para la página actual
        cursor.execute("""
            SELECT problem_id, problem_title, tier, tags, solved_count, level, accepted_user_count, average_tries
            FROM problems
            ORDER BY problem_id::integer
            LIMIT %s OFFSET %s
        """, (per_page, offset))
        
        problems = [
            {
                'id': row[0],
                'title': row[1],
                'tier': row[2],
                'tags': row[3],
                'solved_count': row[4],
                'level': row[5],
                'accepted_user_count': row[6],
                'average_tries': row[7]
            }
            for row in cursor.fetchall()
        ]
        
        cursor.close()
        conn.close()
        
        # Calcular información de paginación
        total_pages = (total + per_page - 1) // per_page
        
    except Exception as e:
        problems = []
        total_pages = 1
        flash(f'Error al obtener la lista de problemas: {str(e)}', 'danger')
    
    return render_template('admin/problem_list.html', 
                          problems=problems,
                          page=page,
                          total_pages=total_pages) 