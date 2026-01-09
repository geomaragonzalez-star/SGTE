@echo off
REM Iniciar servidor FastAPI para SGTE (Nueva Arquitectura)
REM Este script se ejecuta en segundo plano sin mostrar ventana

REM Cambiar al directorio raíz
cd /d %~dp0

REM Activar entorno virtual
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
) else (
    msg * ERROR: Entorno virtual no encontrado. Ejecuta: python -m venv venv
    exit /b 1
)

REM Verificar dependencias
python -c "import fastapi, uvicorn, jinja2" 2>nul
if errorlevel 1 (
    python -m pip install -q -r requirements_backend.txt
)

REM Esperar un momento y abrir el navegador
start "" "http://localhost:8000"

REM Iniciar servidor en segundo plano (sin ventana visible)
start /min "" python -m uvicorn backend.api.main:app --reload --host 0.0.0.0 --port 8000

REM Esperar un poco para que el servidor inicie antes de abrir el navegador
timeout /t 3 /nobreak >nul

REM Abrir navegador (por si acaso no se abrió antes)
start "" "http://localhost:8000"

exit
