import os

# Ruta de la base de datos
# En producción usará el volumen persistente, en desarrollo usará la ruta local
if os.environ.get('FLASK_ENV') == 'production' or os.environ.get('USE_PERSISTENT_DB') == 'true':
    # Verificar si estamos en entorno de desarrollo tratando de usar /data
    if os.environ.get('FLASK_ENV') != 'production' and '/data' in os.environ.get('DATABASE_PATH', '/data/app.db'):
        # En desarrollo local crear un directorio simulado
        data_dir = os.path.join(os.getcwd(), 'data_local')
        if not os.path.exists(data_dir):
            try:
                os.makedirs(data_dir)
            except:
                pass
        DATABASE_PATH = os.path.join(data_dir, 'app.db')
    else:
        DATABASE_PATH = os.environ.get('DATABASE_PATH', '/data/app.db')
else:
    DATABASE_PATH = 'app.db' 