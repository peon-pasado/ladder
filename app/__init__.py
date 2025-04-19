from flask import Flask
from flask_login import LoginManager
import os
from app.models.user import User
from app.config import DATABASE_URL

login_manager = LoginManager()
login_manager.login_view = 'auth.login'

@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')
    
    # Siempre usar la URL de conexión configurada (ahora siempre PostgreSQL en Render)
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
    print(f"APP: Usando base de datos con URI: {DATABASE_URL}")
    
    login_manager.init_app(app)
    
    # Registrar blueprints
    from app.routes.auth import auth
    from app.routes.main import main
    from app.routes.admin import admin
    
    app.register_blueprint(auth)
    app.register_blueprint(main)
    app.register_blueprint(admin, url_prefix='/admin')
    
    return app 