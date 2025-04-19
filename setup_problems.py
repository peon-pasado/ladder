#!/usr/bin/env python
import os
import sys
import psycopg2
from flask import Flask, redirect, url_for, request, render_template_string

app = Flask(__name__)

@app.route('/')
def index():
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
        
        <h2>Acciones de administración</h2>
        <form action="/setup-baekjoon" method="post">
            <button class="button">Configurar cuenta Baekjoon para Admin</button>
        </form>
        
        <form action="/add-example-problems" method="post">
            <button class="button">Añadir problemas de ejemplo</button>
        </form>
        
        <form action="/reset-problems" method="post">
            <button class="button warning">Reiniciar todos los problemas</button>
        </form>
        
        <p>Nota: Todas las operaciones se realizan para el usuario administrador (ID: 1)</p>
    </body>
    </html>
    ''')

@app.route('/setup-baekjoon', methods=['POST'])
def setup_baekjoon():
    try:
        conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
        cursor = conn.cursor()
        
        # Verificar si el usuario admin existe
        cursor.execute("SELECT id FROM users WHERE username = 'admin'")
        admin = cursor.fetchone()
        
        if not admin:
            return render_template_string('''
            <!DOCTYPE html>
            <html>
            <head>
                <title>Error</title>
                <style>body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; } .error { color: red; }</style>
            </head>
            <body>
                <h1 class="error">Error: Usuario admin no encontrado</h1>
                <p>Debes crear un usuario admin primero usando create_admin.py</p>
                <a href="/">Volver</a>
            </body>
            </html>
            ''')
        
        admin_id = admin[0]
        
        # Configurar cuenta de Baekjoon para el admin
        cursor.execute("""
        INSERT INTO baekjoon_accounts (user_id, baekjoon_username) 
        VALUES (%s, 'admin_baekjoon') 
        ON CONFLICT (user_id, baekjoon_username) DO NOTHING
        """, (admin_id,))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return render_template_string('''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Éxito</title>
            <style>body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; } .success { color: green; }</style>
        </head>
        <body>
            <h1 class="success">Cuenta Baekjoon configurada</h1>
            <p>Se ha configurado la cuenta Baekjoon 'admin_baekjoon' para el usuario admin.</p>
            <a href="/">Volver</a>
        </body>
        </html>
        ''')
    except Exception as e:
        return render_template_string(f'''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Error</title>
            <style>body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }} .error {{ color: red; }}</style>
        </head>
        <body>
            <h1 class="error">Error</h1>
            <p>{str(e)}</p>
            <a href="/">Volver</a>
        </body>
        </html>
        ''')

@app.route('/add-example-problems', methods=['POST'])
def add_example_problems():
    try:
        conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
        cursor = conn.cursor()
        
        # Verificar si existe la cuenta baekjoon para admin
        cursor.execute("SELECT id FROM baekjoon_accounts WHERE baekjoon_username = 'admin_baekjoon'")
        account = cursor.fetchone()
        
        if not account:
            return render_template_string('''
            <!DOCTYPE html>
            <html>
            <head>
                <title>Error</title>
                <style>body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; } .error { color: red; }</style>
            </head>
            <body>
                <h1 class="error">Error: Cuenta Baekjoon no encontrada</h1>
                <p>Primero debes configurar una cuenta Baekjoon para el admin.</p>
                <a href="/">Volver</a>
            </body>
            </html>
            ''')
        
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
        
        return render_template_string(f'''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Éxito</title>
            <style>body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }} .success {{ color: green; }}</style>
        </head>
        <body>
            <h1 class="success">Problemas añadidos</h1>
            <p>Se han configurado {problem_count} problemas de ejemplo para la cuenta Baekjoon 'admin_baekjoon'.</p>
            <p>Ahora puedes acceder a tu ladder en <a href="/account/1/ladder">/account/1/ladder</a></p>
            <a href="/">Volver</a>
        </body>
        </html>
        ''')
    except Exception as e:
        return render_template_string(f'''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Error</title>
            <style>body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }} .error {{ color: red; }}</style>
        </head>
        <body>
            <h1 class="error">Error</h1>
            <p>{str(e)}</p>
            <a href="/">Volver</a>
        </body>
        </html>
        ''')

@app.route('/reset-problems', methods=['POST'])
def reset_problems():
    try:
        conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
        cursor = conn.cursor()
        
        # Eliminar todos los problemas del ladder
        cursor.execute("DELETE FROM ladder_problems")
        count = cursor.rowcount
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return render_template_string(f'''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Éxito</title>
            <style>body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }} .success {{ color: green; }}</style>
        </head>
        <body>
            <h1 class="success">Problemas reiniciados</h1>
            <p>Se han eliminado {count} problemas del ladder.</p>
            <a href="/">Volver</a>
        </body>
        </html>
        ''')
    except Exception as e:
        return render_template_string(f'''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Error</title>
            <style>body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }} .error {{ color: red; }}</style>
        </head>
        <body>
            <h1 class="error">Error</h1>
            <p>{str(e)}</p>
            <a href="/">Volver</a>
        </body>
        </html>
        ''')

if __name__ == '__main__':
    app.run(debug=True, port=8000) 