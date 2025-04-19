from app import create_app

# Crear la instancia de la aplicación para que Gunicorn la use directamente
application = create_app()

# Para compatibilidad
app = application

if __name__ == "__main__":
    app.run() 