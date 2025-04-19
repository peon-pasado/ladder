import os

# Configuración de base de datos
# Detecta automáticamente si usar PostgreSQL o SQLite

# SOLUCIÓN FORZADA: Siempre usar PostgreSQL en Render
DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://ladder_db_user:password@host/ladder_db')
DB_TYPE = 'postgresql'
DATABASE_PATH = 'app.db'  # Solo para desarrollo local

print(f"CONFIG: Usando {DB_TYPE} con URL: {DATABASE_URL}")

# Otras configuraciones
SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key-change-in-production') 