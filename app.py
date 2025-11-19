from app import create_app

app = create_app()

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 Ladder App - Servidor de Desarrollo")
    print("="*60)
    print("✓ Base de datos: SQLite (app.db)")
    print("✓ URL: http://localhost:5000")
    print("="*60)
    print("\n👉 Abre tu navegador en: http://localhost:5000\n")
    app.run(debug=True, host='127.0.0.1', port=5000) 