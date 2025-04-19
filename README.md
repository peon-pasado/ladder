# Ladder App

Aplicación para practicar problemas de programación de forma progresiva.

## Funcionalidades

- Sistema de ladders (escaleras) para resolver problemas de programación progresivamente
- Seguimiento de problemas resueltos
- Sincronización con cuentas de Baekjoon
- Integración con la API de Solved.ac para obtener información detallada de los problemas

## Estructura del proyecto

- `app.py`: Punto de entrada de la aplicación Flask
- `app/`: Paquete principal de la aplicación
  - `__init__.py`: Configuración de la aplicación Flask
  - `models/`: Modelos de datos
  - `routes/`: Rutas y controladores
  - `templates/`: Plantillas HTML
  - `static/`: Archivos estáticos (CSS, JS, etc.)
  - `utils/`: Utilidades y herramientas
    - `solved_ac_api.py`: Cliente para la API de Solved.ac
- `init_db.py`: Script para inicializar la base de datos
- `add_problem_ranges.py`: Script para agregar rangos de problemas a la base de datos
- `add_manual_problem_ranges.py`: Script para agregar rangos de problemas con información de tiers
- `update_problems_info.py`: Script para actualizar la información de problemas existentes
- `migrate_problems_table.py`: Script para migrar la estructura de la tabla de problemas

## Integración con Solved.ac API

La aplicación utiliza la API de Solved.ac para obtener información detallada sobre los problemas de programación. La información obtenida incluye:

- Título del problema en varios idiomas
- Nivel de dificultad (tier)
- Etiquetas (tags) que categorizan el problema
- Cantidad de usuarios que han resuelto el problema
- Número promedio de intentos

### Scripts para gestionar problemas

1. `add_problem_ranges.py`: Agrega rangos específicos de problemas y los enriquece con datos de Solved.ac
2. `add_manual_problem_ranges.py`: Permite agregar rangos de problemas con tiers asignados manualmente
3. `update_problems_info.py`: Actualiza la información de problemas existentes en la base de datos

### API de Solved.ac

Se han implementado los siguientes endpoints de la API:

- `GET /problem/lookup`: Consulta información de múltiples problemas por sus IDs
- `GET /problem/show`: Obtiene detalles de un problema específico
- `GET /problem/search`: Busca problemas por criterios como tier, tags, etc.

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

3. (Opcional) Agrega problemas a la base de datos:
   ```bash
   python add_problem_ranges.py
   ```

4. (Opcional) Agrega problemas con tiers manuales:
   ```bash
   python add_manual_problem_ranges.py
   ```

5. Inicia la aplicación:
   ```bash
   python app.py
   ```

## Requisitos

- Python 3.7+
- SQLite
- Flask

## Despliegue en Render

Para desplegar esta aplicación en Render:

1. Asegúrate de tener una cuenta en [Render](https://render.com/)
2. Conecta tu repositorio de GitHub a Render
3. Crea un nuevo Web Service y selecciona el repositorio
4. Usa las siguientes configuraciones:
   - **Environment**: Python
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
   - **Plan**: Free
5. Añade las siguientes variables de entorno:
   - `SECRET_KEY`: Un valor aleatorio y seguro
   - `FLASK_ENV`: production

La aplicación estará disponible en la URL proporcionada por Render una vez que se complete el despliegue.

## Características

- Sistema de autenticación (registro e inicio de sesión)
- Dashboard básico
- Base de datos SQLite
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
   pip install flask flask-login flask-wtf email_validator
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

## Estructura del proyecto

```
ladder-app/
├── app/
│   ├── models/
│   │   └── user.py
│   ├── routes/
│   │   ├── auth.py
│   │   └── main.py
│   ├── static/
│   │   └── css/
│   │       └── style.css
│   ├── templates/
│   │   ├── base.html
│   │   ├── dashboard.html
│   │   ├── index.html
│   │   ├── login.html
│   │   └── register.html
│   └── __init__.py
├── venv/
├── app.db
├── app.py
├── init_db.py
└── README.md
``` 