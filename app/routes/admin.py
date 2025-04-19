from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, render_template_string
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Email
from app.models.user import User
import os
import psycopg2
from app.config import DATABASE_URL

admin = Blueprint('admin', __name__)

class WhitelistForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    notes = TextAreaField('Notas')
    submit = SubmitField('Añadir a la Whitelist')

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
        
        # Crear algunos problemas de ejemplo
        problem_count = 0
        for i in range(1, 11):
            cursor.execute("""
            INSERT INTO ladder_problems (baekjoon_username, position, problem_id, problem_title, state)
            VALUES ('admin_baekjoon', %s, %s, %s, 'visible')
            ON CONFLICT (baekjoon_username, position) DO UPDATE 
            SET problem_id = EXCLUDED.problem_id, 
                problem_title = EXCLUDED.problem_title,
                state = EXCLUDED.state
            """, (i, f"100{i}", f"Problema de ejemplo {i}"))
            problem_count += 1
        
        conn.commit()
        cursor.close()
        conn.close()
        
        flash(f'Se han configurado {problem_count} problemas de ejemplo.', 'success')
        
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