import os
import sys

# Detectar si estamos en Render o si existe DATABASE_URL
IN_RENDER = os.environ.get('RENDER') == 'true' or os.environ.get('DATABASE_URL') is not None

# Valores por defecto (siempre definidos)
DATABASE_PATH = 'app.db'
DB_TYPE = 'sqlite'

# Configuración de base de datos
if IN_RENDER or os.environ.get('DATABASE_URL'):
    # En Render o con URL de base de datos, usar PostgreSQL
    if not os.environ.get('DATABASE_URL'):
        print("ERROR: No se encontró DATABASE_URL en el entorno de producción")
        print("Verifica que la base de datos esté correctamente configurada")
        sys.exit(1)
    
    DATABASE_URL = os.environ.get('DATABASE_URL')
    DB_TYPE = 'postgresql'
    print(f"Usando PostgreSQL con URL: {DATABASE_URL}")
else:
    # En desarrollo local, usar SQLite
    DATABASE_URL = f'sqlite:///{DATABASE_PATH}'
    print(f"Usando SQLite en desarrollo: {DATABASE_PATH}")

# Otras configuraciones
SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key-change-in-production') 