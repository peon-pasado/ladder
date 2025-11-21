from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, render_template_string
from flask_login import login_required, current_user
from flask_wtf import FlaskForm, CSRFProtect
from flask_wtf.csrf import generate_csrf
from wtforms import StringField, TextAreaField, SubmitField, IntegerField
from wtforms.validators import DataRequired, Email, NumberRange
from app.models.user import User
from app.models.ladder_problem import LadderProblem
from app.db import Database
from app.utils.solved_ac_api import SolvedAcAPI
import os
import logging
from app.config import DATABASE_URL, DB_TYPE

# Importar psycopg2 solo si se va a usar PostgreSQL
if DB_TYPE == 'postgresql':
    import psycopg2

# Configurar logging para depuración
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

admin = Blueprint('admin', __name__)

# Función helper para obtener conexión según el tipo de BD
def get_db_connection():
    """Retorna una conexión a la base de datos según el tipo configurado"""
    if DB_TYPE == 'postgresql':
        return psycopg2.connect(DATABASE_URL)
    else:
        import sqlite3
        return sqlite3.connect('app.db')

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

class GroupImportForm(FlaskForm):
    query = StringField('Query de búsqueda', validators=[DataRequired()])
    max_problems = IntegerField('Máximo de problemas', validators=[DataRequired(), NumberRange(min=1, max=1000)])
    submit = SubmitField('Importar Grupo')

@admin.route('/')
@login_required
def admin_index():
    # Verificar si el usuario es admin
    if not current_user.is_admin:
        flash('Acceso denegado. Solo administradores pueden acceder a esta sección.', 'danger')
        return redirect(url_for('main.index'))
    
    # Lista de emails en la whitelist
    whitelist = User.get_whitelist()
    
    return render_template('admin/index.html', whitelist=whitelist)

@admin.route('/whitelist/add', methods=['POST'])
@login_required
def add_to_whitelist():
    # Verificar si el usuario es admin
    if not current_user.is_admin:
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
    if not current_user.is_admin:
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
    if not current_user.is_admin:
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
    if not current_user.is_admin:
        flash('Acceso denegado.', 'danger')
        return redirect(url_for('admin.setup_page'))
    
    try:
        conn = get_db_connection()
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
    if not current_user.is_admin:
        flash('Acceso denegado.', 'danger')
        return redirect(url_for('admin.setup_page'))
    
    try:
        conn = get_db_connection()
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
    if not current_user.is_admin:
        flash('Acceso denegado.', 'danger')
        return redirect(url_for('admin.setup_page'))
    
    try:
        conn = get_db_connection()
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
    # Log para depuración
    logger.debug("Accediendo a la ruta /problems")
    
    # Verificar si el usuario es admin
    if not current_user.is_admin:
        flash('Acceso denegado. Solo administradores pueden acceder a esta sección.', 'danger')
        return redirect(url_for('main.index'))
    
    # Preparar los formularios
    range_form = ProblemRangeForm()
    single_form = SingleProblemForm()
    
    # Obtener los últimos 20 problemas para mostrar en la página
    try:
        conn = get_db_connection()
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
        logger.debug(f"Problemas encontrados: {len(recent_problems)}, Total: {total_problems}")
        
    except Exception as e:
        logger.error(f"Error al cargar problemas: {str(e)}")
        recent_problems = []
        total_problems = 0
        flash(f'Error al obtener problemas: {str(e)}', 'danger')
    
    return render_template('admin/problems.html', 
                          range_form=range_form, 
                          single_form=single_form,
                          recent_problems=recent_problems,
                          total_problems=total_problems)

# Ruta alternativa para depuración
@admin.route('/debug_problems', endpoint='debug_problems_alt')
@login_required
def debug_problems():
    logger.debug("Accediendo a la ruta alternativa /debug_problems")
    if not current_user.is_admin:
        flash('Acceso denegado.', 'danger')
        return redirect(url_for('main.index'))
    
    return render_template('admin/problems.html', 
                          range_form=ProblemRangeForm(),
                          single_form=SingleProblemForm(),
                          recent_problems=[], 
                          total_problems=0)

# Función para inicializar la tabla de problemas
def initialize_problems_table():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Verificar si la tabla problems existe
        cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = 'problems'
        )
        """)
        
        table_exists = cursor.fetchone()[0]
        
        if not table_exists:
            logger.info("Creando tabla 'problems'...")
            
            # Crear la tabla problems si no existe
            cursor.execute("""
            CREATE TABLE problems (
                id SERIAL PRIMARY KEY,
                problem_id TEXT UNIQUE NOT NULL,
                problem_title TEXT NOT NULL,
                tier INTEGER DEFAULT NULL,
                tags TEXT DEFAULT NULL,
                solved_count INTEGER DEFAULT 0,
                level INTEGER DEFAULT NULL,
                accepted_user_count INTEGER DEFAULT 0,
                average_tries REAL DEFAULT 0.0,
                source_group TEXT DEFAULT NULL
            )
            """)
            
            conn.commit()
            logger.info("Tabla 'problems' creada exitosamente")
        else:
            logger.info("La tabla 'problems' ya existe")
        
        cursor.close()
        conn.close()
        return True
    
    except Exception as e:
        logger.error(f"Error al inicializar la tabla problems: {str(e)}")
        return False

@admin.route('/problems/init', methods=['GET', 'POST'])
@login_required
def init_problems_table():
    # Verificar si el usuario es admin
    if not current_user.is_admin:
        flash('Acceso denegado.', 'danger')
        return redirect(url_for('admin.admin_index'))
    
    if request.method == 'POST':
        if initialize_problems_table():
            flash('La tabla "problems" ha sido inicializada correctamente.', 'success')
        else:
            flash('Error al inicializar la tabla "problems".', 'danger')
        return redirect(url_for('admin.gestionar_problemas'))
    
    return render_template_string('''
    {% extends "base.html" %}
    
    {% block title %}Inicializar Tabla de Problemas{% endblock %}
    
    {% block content %}
    <div class="container mt-4">
        <h2>Inicializar Tabla de Problemas</h2>
        
        <div class="alert alert-warning">
            <p><strong>Atención:</strong> Se requiere inicializar la tabla de problemas antes de usar las funciones de gestión.</p>
            <p>El error "relation 'problems' does not exist" indica que esta tabla no existe en la base de datos.</p>
        </div>
        
        <div class="card">
            <div class="card-header bg-primary text-white">
                <h5 class="m-0">Inicialización de la Base de Datos</h5>
            </div>
            <div class="card-body">
                <p>Este proceso creará la tabla necesaria para almacenar los problemas en la base de datos.</p>
                
                <form method="POST" onsubmit="return confirm('¿Estás seguro que deseas inicializar la tabla de problemas?');">
                    <input type="hidden" name="csrf_token" value="{{ csrf_token }}" />
                    <div class="d-grid">
                        <button type="submit" class="btn btn-primary">Inicializar Tabla de Problemas</button>
                    </div>
                </form>
            </div>
        </div>
        
        <div class="mt-3">
            <a href="{{ url_for('admin.admin_index') }}" class="btn btn-secondary">Volver al Panel de Administración</a>
        </div>
    </div>
    {% endblock %}
    ''', csrf_token=generate_csrf())

# Modificar la ruta de gestionar_problemas para verificar y notificar si la tabla no existe
@admin.route('/gestionar_problemas')
@login_required
def gestionar_problemas():
    logger.debug("Accediendo a la ruta simplificada /gestionar_problemas")
    if not current_user.is_admin:
        flash('Acceso denegado.', 'danger')
        return redirect(url_for('main.index'))
    
    # Verificar si la tabla problems existe
    table_exists = False
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if DB_TYPE == 'postgresql':
            cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'problems'
            )
            """)
            table_exists = cursor.fetchone()[0]
        else:
            cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='problems'
            """)
            table_exists = bool(cursor.fetchone())
        
        cursor.close()
        conn.close()
            
    except Exception as e:
        logger.error(f"Error al verificar la tabla problems: {str(e)}")
        flash(f'Error al verificar la base de datos: {str(e)}', 'danger')
    
    # Renderizar un template simplificado directamente
    return render_template_string('''
    {% extends "base.html" %}
    
    {% block title %}Gestión de Problemas{% endblock %}
    
    {% block content %}
    <div class="container mt-4">
        <h2>Gestión de Problemas (Versión Simplificada)</h2>
        
        {% if not ''' + str(table_exists) + ''' %}
        <div class="alert alert-warning">
            <p><strong>Atención:</strong> La tabla "problems" no existe en la base de datos.</p>
            <p>Debe inicializarla antes de poder gestionar problemas.</p>
            <a href="{{ url_for('admin.init_problems_simple') }}" class="btn btn-primary">
                Inicializar Tabla Problems
            </a>
        </div>
        {% endif %}
        
        <div class="row mb-4">
            <div class="col-md-4">
                <div class="card">
                    <div class="card-header bg-info text-white">
                        <h5 class="m-0"><i class="bi bi-plus-circle"></i> Agregar Problema Individual</h5>
                    </div>
                    <div class="card-body">
                        <form method="POST" action="{{ url_for('admin.add_single_problem') }}">
                            <input type="hidden" name="csrf_token" value="{{ csrf_token }}" />
                            <div class="mb-3">
                                <label for="problem_id" class="form-label">ID del Problema</label>
                                <input type="number" class="form-control" id="problem_id" name="problem_id" min="1000" required placeholder="Ej: 1000">
                            </div>
                            <div class="d-grid">
                                <button type="submit" class="btn btn-primary">Agregar Problema</button>
                            </div>
                        </form>
                    </div>
                </div>
            </div>
            
            <div class="col-md-4">
                <div class="card">
                    <div class="card-header bg-success text-white">
                        <h5 class="m-0"><i class="bi bi-list-ol"></i> Agregar Rango de Problemas</h5>
                    </div>
                    <div class="card-body">
                        <form method="POST" action="{{ url_for('admin.add_problem_range') }}">
                            <input type="hidden" name="csrf_token" value="{{ csrf_token }}" />
                            <div class="row">
                                <div class="col-md-6 mb-3">
                                    <label for="start_id" class="form-label">ID Inicio</label>
                                    <input type="number" class="form-control" id="start_id" name="start_id" min="1000" required placeholder="Ej: 1000">
                                </div>
                                <div class="col-md-6 mb-3">
                                    <label for="end_id" class="form-label">ID Fin</label>
                                    <input type="number" class="form-control" id="end_id" name="end_id" min="1000" required placeholder="Ej: 1010">
                                </div>
                            </div>
                            <div class="d-grid">
                                <button type="submit" class="btn btn-success">Agregar Rango</button>
                            </div>
                        </form>
                    </div>
                </div>
            </div>
            
            <div class="col-md-4">
                <div class="card">
                    <div class="card-header bg-warning text-white">
                        <h5 class="m-0"><i class="bi bi-collection"></i> Importar por Grupo</h5>
                    </div>
                    <div class="card-body">
                        <form method="POST" action="{{ url_for('admin.import_problem_group') }}">
                            <input type="hidden" name="csrf_token" value="{{ csrf_token }}" />
                            <div class="mb-3">
                                <label for="query" class="form-label">Query de búsqueda</label>
                                <input type="text" class="form-control" id="query" name="query" required placeholder="Ej: /ptzsum19">
                                <small class="form-text text-muted">
                                    Ejemplos: /ptzsum19, /ptzwin20
                                </small>
                            </div>
                            <div class="mb-3">
                                <label for="max_problems" class="form-label">Máximo de problemas</label>
                                <input type="number" class="form-control" id="max_problems" name="max_problems" min="1" max="1000" value="100" required>
                            </div>
                            <div class="d-grid">
                                <button type="submit" class="btn btn-warning">Importar Grupo</button>
                            </div>
                        </form>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="alert alert-info">
            <h6><i class="bi bi-info-circle"></i> Ejemplos de queries de grupos:</h6>
            <ul class="mb-0">
                <li><strong>/ptzsum19</strong> - Petrozavodsk Summer 2019</li>
                <li><strong>/ptzwin20</strong> - Petrozavodsk Winter 2020</li>
                <li><strong>/ptzsum21</strong> - Petrozavodsk Summer 2021</li>
                <li><strong>tier:15..20</strong> - Problemas entre tier 15 y 20</li>
                <li><strong>*dp</strong> - Problemas con tag de programación dinámica</li>
            </ul>
            <p class="mb-0 mt-2">
                <a href="https://solved.ac/search" target="_blank" class="text-decoration-none">
                    <i class="bi bi-box-arrow-up-right"></i> Ver más opciones de búsqueda en Solved.ac
                </a>
            </p>
        </div>
        
        <div class="d-grid gap-2">
            <a href="{{ url_for('admin.lista_problemas') }}" class="btn btn-outline-primary">Ver Todos los Problemas</a>
            <a href="{{ url_for('admin.admin_index') }}" class="btn btn-outline-secondary">Volver al Panel Admin</a>
            
            <div class="mt-4">
                <a href="{{ url_for('admin.diagnostico_csrf') }}" class="btn btn-outline-info btn-sm">
                    Diagnosticar CSRF
                </a>
                <a href="{{ url_for('admin.debug_problems_direct') }}" class="btn btn-danger btn-sm">
                    Diagnosticar Tabla Problems (Directo)
                </a>
            </div>
        </div>
    </div>
    {% endblock %}
    ''', csrf_token=generate_csrf())

@admin.route('/problems/add-single', methods=['POST'])
@login_required
def add_single_problem():
    # Verificar si el usuario es admin
    if not current_user.is_admin:
        flash('Acceso denegado.', 'danger')
        return redirect(url_for('admin.admin_index'))
    
    # Verificar si la tabla problems existe
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = 'problems'
        )
        """)
        
        table_exists = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        
        if not table_exists:
            flash('La tabla "problems" no existe. Por favor, inicialícela primero.', 'warning')
            return redirect(url_for('admin.init_problems_simple'))
            
    except Exception as e:
        logger.error(f"Error al verificar la tabla problems: {str(e)}")
        flash(f'Error al verificar la base de datos: {str(e)}', 'danger')
        return redirect(url_for('admin.gestionar_problemas'))
    
    # Log para depuración
    logger.debug("Procesando formulario de problema individual")
    
    # Obtener el ID del problema directamente del formulario
    problem_id = request.form.get('problem_id')
    
    if not problem_id:
        flash('El ID del problema es requerido.', 'danger')
        return redirect(url_for('admin.gestionar_problemas'))
    
    try:
        # Obtener información del problema desde Solved.ac
        problem_info = LadderProblem.get_problem_info_from_solved_ac(str(problem_id))
        
        if problem_info:
            # Verificar que el problema se guardó correctamente
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Verificar si el problema se agregó a la BD
            if DB_TYPE == 'postgresql':
                cursor.execute("SELECT problem_id FROM problems WHERE problem_id = %s", (str(problem_id),))
            else:
                cursor.execute("SELECT problem_id FROM problems WHERE problem_id = ?", (str(problem_id),))
            exists = cursor.fetchone()
            
            if exists:
                flash(f'Problema "{problem_info["title"]}" (ID: {problem_id}) agregado correctamente.', 'success')
                logger.debug(f"Problema agregado: {problem_id}, {problem_info['title']}")
            else:
                # Intentar agregarlo manualmente
                if DB_TYPE == 'postgresql':
                    cursor.execute(
                        """
                        INSERT INTO problems 
                        (problem_id, problem_title, tier, tags, solved_count, level, 
                         accepted_user_count, average_tries) 
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        (
                            problem_id, 
                            problem_info["title"], 
                            problem_info.get("tier", 0), 
                            problem_info.get("tags", ""), 
                            problem_info.get("solved_count", 0),
                            problem_info.get("level", 0),
                            problem_info.get("accepted_user_count", 0),
                            problem_info.get("average_tries", 0.0)
                        )
                    )
                else:
                    cursor.execute(
                        """
                        INSERT INTO problems 
                        (problem_id, problem_title, tier, tags, solved_count, level, 
                         accepted_user_count, average_tries) 
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            problem_id, 
                            problem_info["title"], 
                            problem_info.get("tier", 0), 
                            problem_info.get("tags", ""), 
                            problem_info.get("solved_count", 0),
                            problem_info.get("level", 0),
                            problem_info.get("accepted_user_count", 0),
                            problem_info.get("average_tries", 0.0)
                        )
                    )
                conn.commit()
                flash(f'Problema "{problem_info["title"]}" (ID: {problem_id}) agregado manualmente.', 'success')
            
            cursor.close()
            conn.close()
        else:
            flash(f'No se pudo obtener información del problema {problem_id}.', 'warning')
            logger.warning(f"No se pudo obtener info del problema: {problem_id}")
    
    except Exception as e:
        flash(f'Error al agregar el problema: {str(e)}', 'danger')
        logger.error(f"Error al agregar problema: {str(e)}")
    
    return redirect(url_for('admin.gestionar_problemas'))

@admin.route('/problems/import-group', methods=['POST'])
@login_required
def import_problem_group():
    # Verificar si el usuario es admin
    if not current_user.is_admin:
        flash('Acceso denegado.', 'danger')
        return redirect(url_for('admin.admin_index'))
    
    # Verificar si la tabla problems existe
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if DB_TYPE == 'postgresql':
            cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'problems'
            )
            """)
        else:
            cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='problems'
            """)
        
        table_exists = cursor.fetchone()[0] if DB_TYPE == 'postgresql' else bool(cursor.fetchone())
        cursor.close()
        conn.close()
        
        if not table_exists:
            flash('La tabla "problems" no existe. Por favor, inicialícela primero.', 'warning')
            return redirect(url_for('admin.init_problems_simple') if DB_TYPE == 'postgresql' else url_for('admin.gestionar_problemas'))
            
    except Exception as e:
        logger.error(f"Error al verificar la tabla problems: {str(e)}")
        flash(f'Error al verificar la base de datos: {str(e)}', 'danger')
        return redirect(url_for('admin.gestionar_problemas'))
    
    # Log para depuración
    logger.debug("Procesando formulario de importación por grupo")
    
    # Obtener valores del formulario
    query = request.form.get('query', '').strip()
    max_problems = request.form.get('max_problems', 100)
    
    if not query:
        flash('La query de búsqueda es requerida.', 'danger')
        return redirect(url_for('admin.gestionar_problemas'))
    
    try:
        max_problems = int(max_problems)
        if max_problems < 1 or max_problems > 1000:
            flash('El máximo de problemas debe estar entre 1 y 1000.', 'danger')
            return redirect(url_for('admin.gestionar_problemas'))
    except ValueError:
        flash('El máximo de problemas debe ser un número válido.', 'danger')
        return redirect(url_for('admin.gestionar_problemas'))
    
    try:
        # Obtener problemas desde Solved.ac
        logger.info(f"Buscando problemas con query: {query}, max: {max_problems}")
        problems = SolvedAcAPI.get_all_problems_by_query(query, max_problems=max_problems)
        
        if not problems:
            flash(f'No se encontraron problemas con la query: {query}', 'warning')
            return redirect(url_for('admin.gestionar_problemas'))
        
        # Insertar problemas en la base de datos
        conn = get_db_connection()
        cursor = conn.cursor()
        
        added_count = 0
        skipped_count = 0
        error_count = 0
        
        for problem in problems:
            try:
                problem_id = str(problem.get('problemId'))
                title = problem.get('titleKo', problem.get('title', 'Sin título'))
                tier = problem.get('level', 0)
                
                # Obtener tags como string
                tags = ','.join([tag.get('key', '') for tag in problem.get('tags', [])])
                
                solved_count = problem.get('acceptedUserCount', 0)
                average_tries = problem.get('averageTries', 0.0)
                
                # Insertar problema (guardando source_group)
                if DB_TYPE == 'postgresql':
                    cursor.execute(
                        """
                        INSERT INTO problems 
                        (problem_id, problem_title, tier, tags, solved_count, level, 
                         accepted_user_count, average_tries, source_group) 
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (problem_id) DO NOTHING
                        """,
                        (
                            problem_id, title, tier, tags, solved_count, tier,
                            solved_count, average_tries, query
                        )
                    )
                else:
                    cursor.execute(
                        """
                        INSERT OR IGNORE INTO problems 
                        (problem_id, problem_title, tier, tags, solved_count, level, 
                         accepted_user_count, average_tries, source_group) 
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            problem_id, title, tier, tags, solved_count, tier,
                            solved_count, average_tries, query
                        )
                    )
                
                if cursor.rowcount > 0:
                    added_count += 1
                else:
                    skipped_count += 1
                    
            except Exception as e:
                logger.warning(f"Error al insertar problema {problem.get('problemId')}: {str(e)}")
                error_count += 1
                conn.rollback()
        
        conn.commit()
        cursor.close()
        conn.close()
        
        # Mostrar resultado
        message = f'Importación completada: {added_count} problemas agregados'
        if skipped_count > 0:
            message += f', {skipped_count} ya existían'
        if error_count > 0:
            message += f', {error_count} errores'
        
        flash(message, 'success' if added_count > 0 else 'info')
        logger.info(f"Importación completada: {added_count} agregados, {skipped_count} omitidos, {error_count} errores")
    
    except Exception as e:
        flash(f'Error al importar grupo de problemas: {str(e)}', 'danger')
        logger.error(f"Error al importar grupo: {str(e)}")
    
    return redirect(url_for('admin.gestionar_problemas'))

@admin.route('/problems/add-range', methods=['POST'])
@login_required
def add_problem_range():
    # Verificar si el usuario es admin
    if not current_user.is_admin:
        flash('Acceso denegado.', 'danger')
        return redirect(url_for('admin.admin_index'))
    
    # Verificar si la tabla problems existe
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = 'problems'
        )
        """)
        
        table_exists = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        
        if not table_exists:
            flash('La tabla "problems" no existe. Por favor, inicialícela primero.', 'warning')
            return redirect(url_for('admin.init_problems_simple'))
            
    except Exception as e:
        logger.error(f"Error al verificar la tabla problems: {str(e)}")
        flash(f'Error al verificar la base de datos: {str(e)}', 'danger')
        return redirect(url_for('admin.gestionar_problemas'))
    
    # Log para depuración
    logger.debug("Procesando formulario de rango de problemas")
    
    # Obtener valores directamente del formulario
    start_id = request.form.get('start_id')
    end_id = request.form.get('end_id')
    
    if not start_id or not end_id:
        flash('Ambos campos de rango son requeridos.', 'danger')
        return redirect(url_for('admin.gestionar_problemas'))
    
    try:
        start_id = int(start_id)
        end_id = int(end_id)
    except ValueError:
        flash('Los IDs deben ser números enteros.', 'danger')
        return redirect(url_for('admin.gestionar_problemas'))
    
    if start_id > end_id:
        flash('El ID de inicio debe ser menor o igual al ID final.', 'danger')
        return redirect(url_for('admin.gestionar_problemas'))
    
    if end_id - start_id > 100:
        flash('El rango no puede contener más de 100 problemas.', 'danger')
        return redirect(url_for('admin.gestionar_problemas'))
    
    try:
        added_count = 0
        problems_added = []
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        for problem_id in range(start_id, end_id + 1):
            logger.debug(f"Procesando problema en rango: {problem_id}")
            problem_info = LadderProblem.get_problem_info_from_solved_ac(str(problem_id))
            
            if problem_info:
                try:
                    # Intentar insertar directamente
                    cursor.execute(
                        """
                        INSERT INTO problems 
                        (problem_id, problem_title, tier, tags, solved_count, level, 
                         accepted_user_count, average_tries) 
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        (
                            str(problem_id), 
                            problem_info["title"], 
                            problem_info.get("tier", 0), 
                            problem_info.get("tags", ""), 
                            problem_info.get("solved_count", 0),
                            problem_info.get("level", 0),
                            problem_info.get("accepted_user_count", 0),
                            problem_info.get("average_tries", 0.0)
                        )
                    )
                    conn.commit()
                    added_count += 1
                    problems_added.append(f"{problem_id} ({problem_info['title']})")
                except Exception as e:
                    # Si hay un error (como duplicado), solo lo registramos
                    logger.warning(f"Error al insertar problema {problem_id}: {str(e)}")
                    conn.rollback()
        
        cursor.close()
        conn.close()
        
        if added_count > 0:
            if added_count <= 5:
                problem_list = ", ".join(problems_added)
                flash(f'Se agregaron {added_count} problemas correctamente: {problem_list}', 'success')
            else:
                flash(f'Se agregaron {added_count} problemas correctamente.', 'success')
        else:
            flash('No se pudo agregar ningún problema. Posiblemente ya existen en la base de datos.', 'warning')
        
        logger.debug(f"Total problemas agregados en rango: {added_count}")
    
    except Exception as e:
        flash(f'Error al agregar el rango de problemas: {str(e)}', 'danger')
        logger.error(f"Error al agregar rango: {str(e)}")
    
    return redirect(url_for('admin.gestionar_problemas'))

@admin.route('/problems/list')
@login_required
def list_all_problems():
    # Verificar si el usuario es admin
    if not current_user.is_admin:
        flash('Acceso denegado. Solo administradores pueden acceder a esta sección.', 'danger')
        return redirect(url_for('main.index'))
    
    # Parámetros de paginación
    page = request.args.get('page', 1, type=int)
    per_page = 50
    offset = (page - 1) * per_page
    
    try:
        conn = get_db_connection()
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

@admin.route('/problems/lista')
@login_required
def lista_problemas():
    # Verificar si el usuario es admin
    if not current_user.is_admin:
        flash('Acceso denegado. Solo administradores pueden acceder a esta sección.', 'danger')
        return redirect(url_for('main.index'))
    
    # Verificar si la tabla problems existe
    table_exists = False
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if DB_TYPE == 'postgresql':
            cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'problems'
            )
            """)
            table_exists = cursor.fetchone()[0]
        else:
            cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='problems'
            """)
            table_exists = bool(cursor.fetchone())
        
        cursor.close()
        conn.close()
        
        if not table_exists:
            flash('La tabla "problems" no existe. Por favor, inicialícela primero.', 'warning')
            return redirect(url_for('admin.init_problems_simple'))
            
    except Exception as e:
        logger.error(f"Error al verificar la tabla problems: {str(e)}")
        flash(f'Error al verificar la base de datos: {str(e)}', 'danger')
    
    # Log para depuración
    logger.debug("Accediendo a la lista simplificada de problemas")
    
    # Parámetros de paginación
    page = request.args.get('page', 1, type=int)
    per_page = 50
    offset = (page - 1) * per_page
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Obtener el total de problemas para la paginación
        cursor.execute("SELECT COUNT(*) FROM problems")
        total = cursor.fetchone()[0]
        
        # Obtener los problemas para la página actual
        if DB_TYPE == 'postgresql':
            cursor.execute("""
                SELECT problem_id, problem_title, tier, tags, solved_count, level, accepted_user_count, average_tries
                FROM problems
                ORDER BY problem_id::integer
                LIMIT %s OFFSET %s
            """, (per_page, offset))
        else:
            cursor.execute("""
                SELECT problem_id, problem_title, tier, tags, solved_count, level, accepted_user_count, average_tries
                FROM problems
                ORDER BY CAST(problem_id AS INTEGER)
                LIMIT ? OFFSET ?
            """, (per_page, offset))
        
        problems = []
        rows = cursor.fetchall()
        
        # Imprimir resultado bruto para depuración
        logger.debug(f"Resultados de la consulta: {len(rows)} filas")
        
        for row in rows:
            # Convertir valores None a valores por defecto para evitar errores
            problem = {
                'id': row[0] if row[0] is not None else '',
                'title': row[1] if row[1] is not None else 'Sin título',
                'tier': row[2] if row[2] is not None else 0,
                'tags': row[3] if row[3] is not None else '',
                'solved_count': row[4] if row[4] is not None else 0,
                'level': row[5] if row[5] is not None else 0,
                'accepted_user_count': row[6] if row[6] is not None else 0,
                'average_tries': row[7] if row[7] is not None else 0.0
            }
            problems.append(problem)
        
        cursor.close()
        conn.close()
        
        # Calcular información de paginación
        total_pages = (total + per_page - 1) // per_page if total > 0 else 1
        logger.debug(f"Mostrando {len(problems)} problemas, página {page}/{total_pages}")
        
        # Calcular rango de páginas para la paginación
        page_start = max(1, page - 2)
        page_end = min(total_pages + 1, page + 3)
        pagination_range = list(range(page_start, page_end))
        
    except Exception as e:
        problems = []
        total_pages = 1
        total = 0
        pagination_range = [1]
        logger.error(f"Error al obtener la lista de problemas: {str(e)}")
        flash(f'Error al obtener la lista de problemas: {str(e)}', 'danger')
    
    # Renderizar un template simplificado directamente
    return render_template_string('''
    {% extends "base.html" %}
    
    {% block title %}Lista de Problemas{% endblock %}
    
    {% block content %}
    <div class="container mt-4">
        <h2>Lista de Problemas</h2>
        
        <div class="mb-3">
            <a href="{{ url_for('admin.gestionar_problemas') }}" class="btn btn-secondary">
                <i class="fas fa-arrow-left"></i> Volver a Gestión
            </a>
            <a href="{{ url_for('admin.admin_index') }}" class="btn btn-primary">
                <i class="fas fa-home"></i> Panel Admin
            </a>
            <a href="{{ url_for('admin.debug_problems_direct') }}" class="btn btn-danger">
                <i class="fas fa-bug"></i> Diagnóstico Directo
            </a>
        </div>
        
        <div class="card mb-4">
            <div class="card-header bg-primary text-white">
                <h5 class="m-0">Problemas en la Base de Datos ({{ total }} en total - Página {{ page }} de {{ total_pages }})</h5>
            </div>
            <div class="card-body">
                {% if problems %}
                <div class="table-responsive">
                    <table class="table table-striped table-hover">
                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>Título</th>
                                <th>Nivel</th>
                                <th>Resueltos</th>
                                <th>Etiquetas</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for problem in problems %}
                            <tr>
                                <td>{{ problem.id }}</td>
                                <td>{{ problem.title }}</td>
                                <td>{{ problem.tier }}</td>
                                <td>{{ problem.solved_count }}</td>
                                <td>
                                    {% if problem.tags %}
                                        {% for tag in problem.tags.split(',')[:3] %}
                                            <span class="badge bg-secondary">{{ tag }}</span>
                                        {% endfor %}
                                        {% if problem.tags.split(',')|length > 3 %}
                                            <span class="badge bg-info">+{{ problem.tags.split(',')|length - 3 }}</span>
                                        {% endif %}
                                    {% endif %}
                                </td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
                
                <!-- Paginación -->
                <nav aria-label="Navegación de páginas">
                    <ul class="pagination justify-content-center">
                        {% if page > 1 %}
                        <li class="page-item">
                            <a class="page-link" href="{{ url_for('admin.lista_problemas', page=page-1) }}">Anterior</a>
                        </li>
                        {% else %}
                        <li class="page-item disabled">
                            <span class="page-link">Anterior</span>
                        </li>
                        {% endif %}
                        
                        {% for p in pagination_range %}
                        <li class="page-item {% if p == page %}active{% endif %}">
                            <a class="page-link" href="{{ url_for('admin.lista_problemas', page=p) }}">{{ p }}</a>
                        </li>
                        {% endfor %}
                        
                        {% if page < total_pages %}
                        <li class="page-item">
                            <a class="page-link" href="{{ url_for('admin.lista_problemas', page=page+1) }}">Siguiente</a>
                        </li>
                        {% else %}
                        <li class="page-item disabled">
                            <span class="page-link">Siguiente</span>
                        </li>
                        {% endif %}
                    </ul>
                </nav>
                {% else %}
                <div class="alert alert-warning">
                    <p>No hay problemas en la base de datos o hubo un error al obtenerlos.</p>
                    <p>Si acabas de agregar problemas y no aparecen aquí, prueba con el diagnóstico directo.</p>
                </div>
                {% endif %}
            </div>
        </div>
    </div>
    {% endblock %}
    ''', 
    problems=problems,
    page=page,
    total_pages=total_pages,
    total=total,
    pagination_range=pagination_range,
    csrf_token=generate_csrf())

@admin.route('/diagnostico-csrf')
@login_required
def diagnostico_csrf():
    """Ruta de diagnóstico para verificar el funcionamiento de CSRF"""
    if not current_user.is_admin:
        flash('Acceso denegado.', 'danger')
        return redirect(url_for('admin.admin_index'))
    
    csrf_token = generate_csrf()
    
    return render_template_string('''
    {% extends "base.html" %}
    
    {% block title %}Diagnóstico CSRF{% endblock %}
    
    {% block content %}
    <div class="container mt-4">
        <h2>Diagnóstico de CSRF</h2>
        
        <div class="alert alert-info">
            <p>Esta página es para diagnosticar problemas con los tokens CSRF.</p>
            <p>Token generado: <code>{{ csrf_token }}</code></p>
        </div>
        
        <div class="card">
            <div class="card-header">Formulario de prueba</div>
            <div class="card-body">
                <form method="POST" action="{{ url_for('admin.procesar_diagnostico') }}">
                    <input type="hidden" name="csrf_token" value="{{ csrf_token }}" />
                    <div class="mb-3">
                        <label>Campo de prueba</label>
                        <input type="text" name="test_field" class="form-control">
                    </div>
                    <button type="submit" class="btn btn-primary">Enviar</button>
                </form>
            </div>
        </div>
        
        <div class="mt-3">
            <a href="{{ url_for('admin.admin_index') }}" class="btn btn-secondary">Volver</a>
        </div>
    </div>
    {% endblock %}
    ''', csrf_token=csrf_token)

@admin.route('/procesar-diagnostico', methods=['POST'])
@login_required
def procesar_diagnostico():
    """Procesa el formulario de diagnóstico"""
    if not current_user.is_admin:
        flash('Acceso denegado.', 'danger')
        return redirect(url_for('admin.admin_index'))
    
    test_field = request.form.get('test_field', '')
    csrf_token = request.form.get('csrf_token', '')
    
    flash(f'Formulario recibido. Campo: {test_field}, CSRF Token: {csrf_token[:10]}...', 'success')
    return redirect(url_for('admin.diagnostico_csrf'))

@admin.route('/init-problems-simple')
@login_required
def init_problems_simple():
    """Versión simplificada para inicializar la tabla de problemas"""
    if not current_user.is_admin:
        flash('Acceso denegado.', 'danger')
        return redirect(url_for('admin.admin_index'))
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Verificar si la tabla problems existe
        if DB_TYPE == 'postgresql':
            cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'problems'
            )
            """)
            table_exists = cursor.fetchone()[0]
        else:
            cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='problems'
            """)
            table_exists = bool(cursor.fetchone())
        
        if not table_exists:
            logger.info("Creando tabla 'problems'...")
            
            # Crear la tabla problems si no existe
            if DB_TYPE == 'postgresql':
                cursor.execute("""
                CREATE TABLE problems (
                    id SERIAL PRIMARY KEY,
                    problem_id TEXT UNIQUE NOT NULL,
                    problem_title TEXT NOT NULL,
                    tier INTEGER DEFAULT NULL,
                    tags TEXT DEFAULT NULL,
                    solved_count INTEGER DEFAULT 0,
                    level INTEGER DEFAULT NULL,
                    accepted_user_count INTEGER DEFAULT 0,
                    average_tries REAL DEFAULT 0.0
                )
                """)
            else:
                cursor.execute("""
                CREATE TABLE problems (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    problem_id TEXT UNIQUE NOT NULL,
                    problem_title TEXT NOT NULL,
                    tier INTEGER DEFAULT NULL,
                    tags TEXT DEFAULT NULL,
                    solved_count INTEGER DEFAULT 0,
                    level INTEGER DEFAULT NULL,
                    accepted_user_count INTEGER DEFAULT 0,
                    average_tries REAL DEFAULT 0.0,
                    source_group TEXT DEFAULT NULL
                )
                """)
            
            conn.commit()
            flash('La tabla "problems" ha sido creada correctamente.', 'success')
            logger.info("Tabla 'problems' creada exitosamente")
        else:
            flash('La tabla "problems" ya existe en la base de datos.', 'info')
            logger.info("La tabla 'problems' ya existe")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        logger.error(f"Error al inicializar la tabla problems: {str(e)}")
        flash(f'Error al inicializar la tabla: {str(e)}', 'danger')
    
    return redirect(url_for('admin.gestionar_problemas'))

@admin.route('/debug-problems-direct')
@login_required
def debug_problems_direct():
    """Diagnóstico directo de la tabla problems"""
    if not current_user.is_admin:
        flash('Acceso denegado.', 'danger')
        return redirect(url_for('admin.admin_index'))
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Verificar si la tabla problems existe
        if DB_TYPE == 'postgresql':
            cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'problems'
            )
            """)
            table_exists = cursor.fetchone()[0]
        else:
            cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='problems'
            """)
            table_exists = bool(cursor.fetchone())
        
        if not table_exists:
            return f"""
            <h2>Diagnóstico de problemas</h2>
            <p style="color: red;">La tabla 'problems' no existe en la base de datos.</p>
            <a href="{url_for('admin.init_problems_simple')}">Inicializar tabla</a>
            """
        
        # Ver estructura de la tabla
        if DB_TYPE == 'postgresql':
            cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'problems'
            """)
        else:
            cursor.execute("PRAGMA table_info(problems)")
        
        structure = cursor.fetchall()
        
        # Contar total de registros
        cursor.execute("SELECT COUNT(*) FROM problems")
        count = cursor.fetchone()[0]
        
        # Ver algunos registros
        cursor.execute("SELECT * FROM problems LIMIT 10")
        records = cursor.fetchall()
        
        # Ver los últimos 5 problemas agregados
        cursor.execute("SELECT * FROM problems ORDER BY id DESC LIMIT 5")
        latest = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        # Generar informe HTML simple
        if DB_TYPE == 'postgresql':
            columns = [col[0] for col in structure]
            structure_rows = [(col[0], col[1]) for col in structure]
        else:
            # Para SQLite, PRAGMA table_info devuelve: cid, name, type, notnull, dflt_value, pk
            columns = [col[1] for col in structure]
            structure_rows = [(col[1], col[2]) for col in structure]
        
        html = f"""
        <html>
        <head>
            <title>Diagnóstico de la tabla problems</title>
            <style>
                body {{ font-family: Arial, sans-serif; padding: 20px; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            <h2>Diagnóstico de la tabla problems</h2>
            
            <h3>Estructura de la tabla:</h3>
            <table>
                <tr>
                    <th>Columna</th>
                    <th>Tipo</th>
                </tr>
                {"".join(f"<tr><td>{col[0]}</td><td>{col[1]}</td></tr>" for col in structure_rows)}
            </table>
            
            <h3>Cantidad de registros: {count}</h3>
            
            <h3>Últimos 5 problemas agregados:</h3>
            <table>
                <tr>
                    {"".join(f"<th>{col}</th>" for col in columns)}
                </tr>
                {"".join(f"<tr>{''.join(f'<td>{str(val)}</td>' for val in row)}</tr>" for row in latest)}
            </table>
            
            <h3>Primeros 10 registros:</h3>
            <table>
                <tr>
                    {"".join(f"<th>{col}</th>" for col in columns)}
                </tr>
                {"".join(f"<tr>{''.join(f'<td>{str(val)}</td>' for val in row)}</tr>" for row in records)}
            </table>
            
            <p><a href="{url_for('admin.gestionar_problemas')}">Volver a Gestión</a></p>
        </body>
        </html>
        """
        
        return html
        
    except Exception as e:
        logger.error(f"Error en diagnóstico de problemas: {str(e)}")
        return f"""
        <h2>Error en diagnóstico</h2>
        <p style="color: red;">{str(e)}</p>
        <a href="{url_for('admin.gestionar_problemas')}">Volver a Gestión</a>
        """ 