import os

# Configuración de base de datos
# Detecta automáticamente si usar PostgreSQL o SQLite

# Si existe DATABASE_URL (proporcionada por Render para PostgreSQL)
if os.environ.get('DATABASE_URL'):
    # Usar PostgreSQL
    DATABASE_URL = os.environ.get('DATABASE_URL')
    DB_TYPE = 'postgresql'
    DATABASE_PATH = None  # No se usa para PostgreSQL
else:
    # Usar SQLite (para desarrollo o en caso de que no haya PostgreSQL)
    DB_TYPE = 'sqlite'
    
    # Ruta de la base de datos SQLite
    if os.environ.get('FLASK_ENV') == 'production' or os.environ.get('USE_PERSISTENT_DB') == 'true':
        # En producción sin PostgreSQL, intentar usar volumen persistente
        if os.environ.get('FLASK_ENV') != 'production' and '/data' in os.environ.get('DATABASE_PATH', '/data/db/app.db'):
            # Simulación local del volumen persistente
            data_dir = os.path.join(os.getcwd(), 'data_local')
            if not os.path.exists(data_dir):
                try:
                    os.makedirs(data_dir)
                except:
                    pass
            DATABASE_PATH = os.path.join(data_dir, 'app.db')
        else:
            DATABASE_PATH = os.environ.get('DATABASE_PATH', '/data/db/app.db')
    else:
        # En desarrollo usar SQLite local
        DATABASE_PATH = 'app.db'
    
    # URL para SQLAlchemy
    DATABASE_URL = f'sqlite:///{DATABASE_PATH}'

# Otras configuraciones
SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key-change-in-production') 