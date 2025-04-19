from flask import Flask
from flask_login import LoginManager
import os
from app.models.user import User
from app.config import DATABASE_PATH, DATABASE_URL, DB_TYPE

login_manager = LoginManager()
login_manager.login_view = 'auth.login'

@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')
    
    # En producción usar PostgreSQL
    if os.environ.get('DATABASE_URL') and os.environ.get('FLASK_ENV') == 'production':
        # Usar PostgreSQL
        app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
        print("Usando PostgreSQL en producción")
    else:
        # Usar SQLite (para desarrollo local)
        app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DATABASE_PATH}'
        print(f"Usando SQLite en desarrollo: {DATABASE_PATH}")
        
        # Solo creamos directorio para SQLite
        db_dir = os.path.dirname(DATABASE_PATH)
        if db_dir and not os.path.exists(db_dir):
            try:
                os.makedirs(db_dir, exist_ok=True)
                print(f"Directorio de base de datos creado: {db_dir}")
            except Exception as e:
                print(f"Error al crear directorio de base de datos: {e}")
    
    login_manager.init_app(app)
    
    # Registrar blueprints
    from app.routes.auth import auth
    from app.routes.main import main
    from app.routes.admin import admin
    
    app.register_blueprint(auth)
    app.register_blueprint(main)
    app.register_blueprint(admin, url_prefix='/admin')
    
    return app 