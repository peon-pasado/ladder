# 🪜 Ladder App

Aplicación web para gestión de problemas de programación competitiva con sistema de escalera (ladder).

## 📋 Requisitos Previos

- Python 3.11 o superior
- pip (gestor de paquetes de Python)
- Git

## 🚀 Instalación

### 1. Clonar el repositorio

```bash
git clone <url-del-repositorio>
cd ladder
```

### 2. Crear entorno virtual

**Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**Windows (Command Prompt):**
```cmd
python -m venv venv
venv\Scripts\activate.bat
```

**Linux/Mac:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

Si `pip install` falla con `psycopg2`, ejecuta:
```bash
pip install blinker certifi charset-normalizer click dnspython email-validator Flask Flask-Login Flask-WTF idna itsdangerous Jinja2 MarkupSafe requests urllib3 Werkzeug WTForms
```

### 4. Inicializar la base de datos (primera vez)

```bash
python init_db.py
```

Esto creará la base de datos `app.db` con el usuario admin por defecto.

## 🎮 Uso

### Ejecución Local

**Opción 1 - Scripts automatizados (Windows):**
```cmd
start_server.cmd
```

**Opción 2 - Comando manual:**
```bash
python run_server.py
```

La aplicación estará disponible en: `http://localhost:5000`

### Acceso desde Internet (con ngrok)

1. Descarga ngrok desde: https://ngrok.com/download
2. Autentícate: `ngrok config add-authtoken TU_TOKEN`
3. Ejecuta:

**Windows:**
```cmd
start_ngrok.cmd
```

**Manual:**
```bash
ngrok http 5000
```

4. Copia la URL pública que aparece en "Forwarding"

## 🔑 Credenciales por Defecto

```
Usuario:    admin
Contraseña: admin123
```

**Nota:** La contraseña por defecto debe cambiarse después de la primera instalación por seguridad.

## 📁 Estructura del Proyecto

```
ladder/
├── app/                    # Aplicación Flask
│   ├── models/            # Modelos de datos
│   ├── routes/            # Rutas y endpoints
│   ├── templates/         # Plantillas HTML
│   ├── static/            # Archivos estáticos (CSS)
│   └── utils/             # Utilidades
├── venv/                  # Entorno virtual (no en git)
├── app.db                 # Base de datos SQLite (no en git)
├── start_server.cmd       # Script de inicio (Windows)
├── start_ngrok.cmd        # Script ngrok (Windows)
├── run_server.py          # Script principal del servidor
└── requirements.txt       # Dependencias
```

## 🛠️ Tecnologías

- **Backend:** Flask (Python)
- **Base de datos:** SQLite
- **Autenticación:** Flask-Login
- **Formularios:** Flask-WTF
- **Frontend:** HTML, CSS, Jinja2
- **API Externa:** solved.ac (para problemas de Baekjoon)

## 🌐 Deploy

### Variables de Entorno (Producción)

```bash
DATABASE_URL=postgresql://...  # URL de PostgreSQL
SECRET_KEY=tu-clave-secreta
RENDER=true                    # Para Render.com
```

### Render.com

El proyecto incluye `render.yaml` para deploy automático en Render.

## 📝 Desarrollo

### Instalar nuevas dependencias

```bash
pip install nombre-paquete
pip freeze > requirements.txt
```

### Base de datos

La base de datos SQLite se crea automáticamente en `app.db` al iniciar la aplicación.

## 🔐 Cambiar Contraseña del Admin

Para cambiar la contraseña del administrador:

```bash
python cambiar_clave_admin.py
```

O proporciona la nueva contraseña directamente:

```bash
python cambiar_clave_admin.py mi_nueva_password
```

## 🐛 Solución de Problemas

### Puerto 5000 ocupado
```bash
# Windows
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# Linux/Mac
lsof -i :5000
kill -9 <PID>
```

### Error de módulos no encontrados
```bash
# Verifica que el entorno virtual esté activado
# Reinstala las dependencias
pip install -r requirements.txt
```

### Error de base de datos
```bash
# Elimina y reinicia la base de datos
rm app.db
python run_server.py
```

## 🤝 Contribuir

1. Fork el proyecto
2. Crea una rama (`git checkout -b feature/nueva-funcionalidad`)
3. Commit tus cambios (`git commit -am 'Agrega nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto es de código abierto.

## 👥 Autores

- Desarrollo inicial y mantenimiento

## 📞 Contacto

Para reportar problemas o sugerencias, abre un issue en el repositorio.

---

**Nota:** Este proyecto está en desarrollo activo. Algunas funcionalidades pueden cambiar.

