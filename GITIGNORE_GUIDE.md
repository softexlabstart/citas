# Guía de Archivos Ignorados en Git

## Archivos y Carpetas que NO deben subirse al repositorio

### 🐍 Python / Django

#### Archivos compilados
- `__pycache__/` - Cache de bytecode de Python
- `*.pyc, *.pyo, *.pyd` - Archivos compilados de Python
- `*.py[cod]` - Variaciones de archivos compilados
- `*$py.class` - Archivos de clase Java

#### Entornos virtuales
- `env/, venv/, ENV/` - Carpetas de entorno virtual
- `env.bak/, venv.bak/` - Backups de entornos

#### Base de datos
- `db.sqlite3, *.sqlite3, *.db` - Bases de datos SQLite (usar dump/fixtures para compartir datos)

#### Archivos de configuración sensibles
- `.env` - Variables de entorno (contiene secrets)
- `.env.local, .env.*.local` - Variantes locales
- `local_settings.py` - Configuración local de Django

#### Archivos generados
- `staticfiles/` - ⚠️ **IMPORTANTE**: Archivos estáticos recopilados por `collectstatic`
- `media/` - Archivos subidos por usuarios
- `*.log` - Archivos de log

#### Celery
- `celerybeat-schedule` - Programación de tareas periódicas
- `celerybeat.pid` - ID de proceso de Celery Beat
- `*.pid, *.sock` - Archivos de procesos

---

### 📦 Node / React / Frontend

#### Dependencias
- `node_modules/` - ⚠️ **MUY IMPORTANTE**: Librerías de Node (se instalan con `npm install`)

#### Build / Dist
- `dist/, build/` - ⚠️ **IMPORTANTE**: Archivos compilados del frontend
- `dist-ssr/` - Server-side rendering build

#### Logs y cache
- `npm-debug.log*, yarn-debug.log*, pnpm-debug.log*` - Logs de gestores de paquetes
- `.npm, .pnp/` - Cache de npm y PnP

#### Variables de entorno
- `.env.local` - Variables locales
- `.env.development.local` - Para desarrollo
- `.env.test.local` - Para testing
- `.env.production.local` - Para producción

#### Otros
- `*.tsbuildinfo` - Info de build de TypeScript
- `vite.config.ts.timestamp-*.mjs` - Timestamps de Vite

---

### 🧪 Testing / Coverage

- `.coverage, .coverage.*` - Reportes de cobertura de Python
- `htmlcov/` - Reporte HTML de cobertura
- `.pytest_cache/` - Cache de pytest
- `.tox/` - Entornos de testing
- `coverage/` - Cobertura de tests JavaScript
- `nosetests.xml, coverage.xml` - Reportes XML

#### Cypress
- `/cypress/videos/` - Videos de tests
- `/cypress/screenshots/` - Screenshots de tests

---

### 💻 Sistema Operativo

#### macOS
- `.DS_Store` - Metadatos de Finder
- `.AppleDouble, .LSOverride` - Archivos de macOS
- `._*` - Archivos de recursos de macOS

#### Windows
- `Thumbs.db, ehthumbs.db` - Caché de miniaturas
- `Desktop.ini` - Configuración de carpetas

---

### 🔧 Editores e IDEs

#### Visual Studio Code
- `.vscode/*` - Configuración del editor
- ⚠️ **EXCEPCIONES** (estos SÍ se pueden subir):
  - `!.vscode/extensions.json`
  - `!.vscode/settings.json` (si son configuraciones compartidas)
  - `!.vscode/tasks.json`
  - `!.vscode/launch.json`

#### JetBrains (PyCharm, WebStorm, IntelliJ)
- `.idea/` - Configuración del proyecto
- `.idea/**/workspace.xml` - Espacio de trabajo
- `.idea/**/tasks.xml` - Tareas
- `.idea/**/dictionaries` - Diccionarios personalizados

#### Otros editores
- `*.swp, *~, *.sw?` - Archivos temporales de Vim
- `*.sublime-workspace` - Workspace de Sublime Text

---

### 🔐 Seguridad y Credenciales

⚠️ **CRÍTICO - NUNCA SUBIR ESTOS ARCHIVOS**

- `*.pem, *.key, *.cert` - Certificados y claves privadas
- `.envrc` - Variables de entorno
- `secrets.json, credentials.json` - Credenciales
- `.env` - Variables de entorno con secrets

---

### 📝 Documentación Temporal

Estos archivos son borradores o documentación de trabajo:
- `MULTITENANCY_README.md` - (ya está en .gitignore)
- `*.draft.md` - Borradores
- `*.wip.md` - Work in progress

---

### 🗑️ Archivos de Backup

- `*.bak, *.backup` - Backups
- `*.tmp` - Archivos temporales
- `*~` - Backups automáticos

---

## ✅ Archivos que SÍ deben subirse

### Backend
- ✅ `requirements.txt` - Dependencias de Python
- ✅ `manage.py` - Script de gestión de Django
- ✅ Todo el código fuente en `backend/`
- ✅ Migraciones de Django (`*/migrations/*.py`)
- ✅ `gunicorn_config.py` - Configuración de Gunicorn
- ✅ `.env.example` - Ejemplo de variables de entorno (sin valores reales)

### Frontend
- ✅ `package.json, package-lock.json` - Dependencias de Node
- ✅ Todo el código fuente en `src/`
- ✅ `public/` - Archivos públicos estáticos
- ✅ `index.html, vite.config.ts` - Configuración

### Documentación
- ✅ `README.md` - Documentación principal
- ✅ `ROLES_Y_PERMISOS.md` - Documentación de roles
- ✅ `DEPLOYMENT_GUIDE.md` - Guía de despliegue
- ✅ `OPTIMIZATIONS_SUMMARY.md` - Resumen de optimizaciones
- ✅ `COLABORADORES_FEATURES.md` - Documentación de features

### Configuración
- ✅ `.gitignore` - Este archivo
- ✅ `GITIGNORE_GUIDE.md` - Esta guía

---

## 🧹 Limpieza de archivos ya trackeados

Si accidentalmente ya subiste archivos que deberían estar en `.gitignore`, usa estos comandos:

### Remover archivos específicos del tracking
```bash
# Remover __pycache__
git rm -r --cached backend/__pycache__
git rm -r --cached backend/*/migrations/__pycache__
git rm -r --cached backend/*/__pycache__

# Remover staticfiles
git rm -r --cached backend/staticfiles

# Remover build del frontend
git rm -r --cached frontend/build

# Remover node_modules (si se subió por error)
git rm -r --cached frontend/node_modules
```

### Remover TODOS los archivos ignorados del tracking
```bash
# ⚠️ CUIDADO: Esto remueve todo lo que coincida con .gitignore
git rm -r --cached .
git add .
git commit -m "Limpiar archivos ignorados del repositorio"
```

---

## 📋 Verificación

Para verificar qué archivos están siendo ignorados:

```bash
# Ver archivos ignorados
git status --ignored

# Ver solo archivos nuevos que serían ignorados
git status --ignored --untracked-files=all

# Verificar si un archivo específico será ignorado
git check-ignore -v archivo.txt
```

---

## 🚀 Mejores Prácticas

1. **Nunca** subir archivos con credenciales o secrets
2. **Nunca** subir `node_modules/` o archivos de build
3. **Siempre** usar `.env.example` para documentar variables de entorno necesarias
4. **Revisar** `git status` antes de cada commit
5. **Usar** `git diff --cached` para revisar cambios antes de commitear
6. **Limpiar** archivos innecesarios periódicamente con `git clean -fdx` (cuidado, esto borra archivos no trackeados)

---

## 📊 Tamaño del Repositorio

Mantener el `.gitignore` actualizado ayuda a:
- ✅ Reducir tamaño del repositorio
- ✅ Acelerar clones y pulls
- ✅ Evitar conflictos de merge en archivos generados
- ✅ Mejorar seguridad (no subir secrets)
- ✅ Facilitar colaboración

---

## ⚠️ Archivos Críticos a Revisar

Antes de cada commit, verifica que NO estás subiendo:

- [ ] `.env` o archivos con variables de entorno
- [ ] `db.sqlite3` o cualquier archivo de base de datos
- [ ] `node_modules/`
- [ ] `staticfiles/` o `media/`
- [ ] `__pycache__/` o archivos `.pyc`
- [ ] Certificados, claves o credenciales
- [ ] Archivos de build (`dist/`, `build/`)
