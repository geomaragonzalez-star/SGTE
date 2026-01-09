@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║         SGTE - Sistema de Gestión de Titulaciones            ║
echo ║                   Instalador v2.0                            ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

:: ============================================
:: PASO 1: Verificar Python
:: ============================================
echo [1/4] Verificando Python...

python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo ╔══════════════════════════════════════════════════════════════╗
    echo ║  [ERROR] Python no está instalado o no está en PATH          ║
    echo ║                                                              ║
    echo ║  Por favor:                                                  ║
    echo ║  1. Descargue Python 3.11+ desde https://python.org         ║
    echo ║  2. Durante la instalación, marque "Add Python to PATH"     ║
    echo ║  3. Reinicie este script                                    ║
    echo ╚══════════════════════════════════════════════════════════════╝
    echo.
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo       [OK] Python %PYTHON_VERSION% detectado.

:: ============================================
:: PASO 2: Crear entorno virtual
:: ============================================
echo.
echo [2/4] Configurando entorno virtual...

if not exist "venv" (
    echo       Creando entorno virtual...
    python -m venv venv
    if errorlevel 1 (
        echo       [ERROR] No se pudo crear el entorno virtual.
        pause
        exit /b 1
    )
    echo       [OK] Entorno virtual creado.
) else (
    echo       [OK] Entorno virtual ya existe.
)

:: ============================================
:: PASO 3: Activar e instalar dependencias
:: ============================================
echo.
echo [3/4] Instalando dependencias...

call venv\Scripts\activate.bat

:: Actualizar pip silenciosamente
python -m pip install --upgrade pip --quiet

:: Instalar dependencias
pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo.
    echo       [ERROR] Error instalando dependencias.
    echo       Revise el archivo requirements.txt
    pause
    exit /b 1
)

echo       [OK] Dependencias instaladas correctamente.

:: ============================================
:: PASO 4: Crear estructura de datos
:: ============================================
echo.
echo [4/4] Creando estructura de datos...

if not exist "data" mkdir data
if not exist "backups" mkdir backups

echo       [OK] Carpetas de datos creadas.

:: ============================================
:: INSTALACIÓN COMPLETADA
:: ============================================
echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║                                                              ║
echo ║            ✓ INSTALACIÓN COMPLETADA CON ÉXITO               ║
echo ║                                                              ║
echo ║  Para iniciar el sistema, ejecute:                          ║
echo ║                                                              ║
echo ║                    run.bat                                   ║
echo ║                                                              ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

pause
