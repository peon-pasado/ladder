import os
import sys

# Detectar si estamos en Render
IN_RENDER = os.environ.get('RENDER') == 'true'

# Configuración de base de datos
if IN_RENDER:
    # En Render, necesitamos DATABASE_URL
    if not os.environ.get('DATABASE_URL'):
        print("ERROR: No se encontró DATABASE_URL en el entorno de Render")
        print("Verifica que la base de datos esté correctamente configurada")
        sys.exit(1)
    
    DATABASE_URL = os.environ.get('DATABASE_URL')
    DB_TYPE = 'postgresql'
    print(f"Usando PostgreSQL en Render con URL de conexión proporcionada")
else:
    # En desarrollo local, usar SQLite
    DB_TYPE = 'sqlite'
    DATABASE_PATH = 'app.db'
    DATABASE_URL = f'sqlite:///{DATABASE_PATH}'
    print(f"Usando SQLite en desarrollo: {DATABASE_PATH}")

# Otras configuraciones
SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key-change-in-production') 