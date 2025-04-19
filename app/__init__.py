from flask import Flask
from flask_login import LoginManager
import os
from app.models.user import User
from app.config import DATABASE_URL, IN_RENDER

login_manager = LoginManager()
login_manager.login_view = 'auth.login'

@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')
    
    # Configurar la base de datos según el entorno
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
    print(f"APP: Configurando conexión a la base de datos con URI: {DATABASE_URL}")
    
    # Debugear entorno Render
    if IN_RENDER:
        print("Estamos en el entorno Render")
        for key, value in os.environ.items():
            if key.startswith('DATABASE_') or key == 'RENDER':
                print(f"ENV: {key}={value}")
    
    login_manager.init_app(app)
    
    # Registrar blueprints
    from app.routes.auth import auth
    from app.routes.main import main
    from app.routes.admin import admin
    
    app.register_blueprint(auth)
    app.register_blueprint(main)
    app.register_blueprint(admin, url_prefix='/admin')
    
    return app 