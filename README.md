# Ladder App

Aplicación para practicar problemas de programación de forma progresiva.

## Funcionalidades

- Sistema de ladders (escaleras) para resolver problemas de programación progresivamente
- Seguimiento de problemas resueltos
- Sincronización con cuentas de Baekjoon
- Integración con la API de Solved.ac para obtener información detallada de los problemas

## Estructura del proyecto

- `app.py`: Punto de entrada de la aplicación Flask
- `wsgi.py`: Punto de entrada para servidores WSGI (Gunicorn)
- `init_db.py`: Script para inicializar la base de datos
- `app/`: Paquete principal de la aplicación
  - `__init__.py`: Configuración de la aplicación Flask
  - `config.py`: Configuración de la aplicación
  - `db.py`: Gestión de conexiones a base de datos
  - `models/`: Modelos de datos (User, BaekjoonAccount, LadderProblem, SolvedProblem)
  - `routes/`: Rutas y controladores (auth, main, admin)
  - `templates/`: Plantillas HTML
  - `static/`: Archivos estáticos (CSS, JS, etc.)
  - `utils/`: Utilidades y herramientas
    - `solved_ac_api.py`: Cliente para la API de Solved.ac
    - `problem_recommender.py`: Sistema de recomendación de problemas
    - `problem_validator.py`: Validador de problemas
    - `rating_calculator.py`: Calculador de rating
- `requirements.txt`: Dependencias del proyecto
- `Procfile`: Configuración para despliegue en Render
- `render.yaml`: Configuración de infraestructura en Render

## Integración con Solved.ac API

La aplicación utiliza la API de Solved.ac para obtener información detallada sobre los problemas de programación. La información obtenida incluye:

- Título del problema en varios idiomas
- Nivel de dificultad (tier)
- Etiquetas (tags) que categorizan el problema
- Cantidad de usuarios que han resuelto el problema
- Número promedio de intentos

## Uso

1. Configura un entorno virtual e instala las dependencias:
   ```bash
   python -m venv venv
   source venv/bin/activate  # En Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. Inicializa la base de datos:
   ```bash
   python init_db.py
   ```

3. Inicia la aplicación:
   ```bash
   python app.py
   ```

## Requisitos

- Python 3.7+
- SQLite o PostgreSQL
- Flask y dependencias (ver requirements.txt)

## Despliegue en Render

Para desplegar esta aplicación en Render:

1. Asegúrate de tener una cuenta en [Render](https://render.com/)
2. Conecta tu repositorio de GitHub a Render
3. Usa el archivo `render.yaml` incluido que configura automáticamente:
   - Un Web Service con Python
   - Una base de datos PostgreSQL
   - Variables de entorno necesarias
4. Render detectará automáticamente la configuración y desplegará la aplicación

La aplicación estará disponible en la URL proporcionada por Render una vez que se complete el despliegue.

## Características

- Sistema de autenticación (registro e inicio de sesión)
- Whitelist de correos electrónicos para registro
- Sistema de ladders personalizados por usuario
- Integración con cuentas de Baekjoon
- Sincronización automática de problemas resueltos
- Sistema de recomendación de problemas basado en dificultad
- Seguimiento de progreso y rating
- Panel de administración
- Base de datos SQLite (desarrollo) o PostgreSQL (producción)
- Diseño responsivo con Bootstrap

## Instalación

1. Clonar este repositorio
2. Crear un entorno virtual:
   ```bash
   python -m venv venv
   ```
3. Activar el entorno virtual:
   - En Windows: `venv\Scripts\activate`
   - En macOS/Linux: `source venv/bin/activate`
4. Instalar las dependencias:
   ```bash
   pip install -r requirements.txt
   ```

## Configuración inicial

1. Inicializar la base de datos:
   ```bash
   python init_db.py
   ```

## Ejecución

1. Ejecutar la aplicación:
   ```bash
   python app.py
   ```
2. Abrir en el navegador: [http://localhost:5000](http://localhost:5000) 