@echo off
REM Iniciar servidor FastAPI para SGTE (Nueva Arquitectura)

echo ========================================
echo   SGTE - FastAPI + Jinja2
echo   Nueva Arquitectura Híbrida
echo ========================================
echo.

REM Activar entorno virtual
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
) else (
    echo ERROR: Entorno virtual no encontrado
    echo Ejecuta: python -m venv venv
    pause
    exit /b 1
)

echo Verificando dependencias...
python -c "import fastapi, uvicorn, jinja2" 2>nul
if errorlevel 1 (
    echo Instalando dependencias adicionales...
    pip install -r requirements_backend.txt
)

echo.
echo Iniciando servidor FastAPI...
echo.
echo ========================================
echo   URLs Disponibles:
echo ========================================
echo   Frontend:     http://localhost:8000
echo   Dashboard:    http://localhost:8000/dashboard
echo   Estudiantes:  http://localhost:8000/estudiantes
echo   Documentos:   http://localhost:8000/documentos
echo   Reportes:     http://localhost:8000/reportes
echo   API Docs:     http://localhost:8000/docs
echo ========================================
echo.

REM Cambiar al directorio raíz para imports correctos
cd /d %~dp0

REM Iniciar servidor
python -m uvicorn backend.api.main:app --reload --host 0.0.0.0 --port 8000

pause
