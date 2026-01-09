@echo off
chcp 65001 >nul
title SGTE - Sistema de Gestión de Titulaciones v2.0

echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║         SGTE - Sistema de Gestión de Titulaciones            ║
echo ║                    Iniciando...                              ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

:: ============================================
:: PASO 1: Forzar ubicación correcta
:: ============================================
echo [1/4] Ubicando directorio de trabajo...
cd /d "C:\Users\YomiT\Documents\Tesis\SGTE"
if errorlevel 1 (
    echo [ERROR] No se pudo acceder al directorio de la aplicación.
    echo         Verifique que la ruta existe: C:\Users\YomiT\Documents\Tesis\SGTE
    pause
    exit /b 1
)
echo       ✓ Directorio: %CD%
echo.

:: ============================================
:: PASO 2: Verificar y activar entorno virtual
:: ============================================
echo [2/4] Activando entorno virtual...
if not exist "venv\Scripts\activate.bat" (
    echo [ERROR] Entorno virtual no encontrado.
    echo         Ejecute primero: install.bat
    echo.
    pause
    exit /b 1
)

call venv\Scripts\activate.bat
if errorlevel 1 (
    echo [ERROR] No se pudo activar el entorno virtual.
    pause
    exit /b 1
)
echo       ✓ Entorno virtual activado
echo.

:: ============================================
:: PASO 3: Verificar Streamlit instalado
:: ============================================
echo [3/4] Verificando dependencias...
streamlit --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Streamlit no está instalado.
    echo         Ejecute: install.bat
    echo.
    pause
    exit /b 1
)
echo       ✓ Streamlit instalado correctamente
echo.

:: ============================================
:: PASO 4: Abrir Chrome y ejecutar Streamlit
:: ============================================
echo [4/4] Iniciando aplicación...
echo.
echo ══════════════════════════════════════════════════════════════
echo   La aplicación se está iniciando en:
echo   → http://localhost:8501
echo.
echo   Para cerrar la aplicación:
echo   • Cierre esta ventana, o
echo   • Presione Ctrl+C
echo ══════════════════════════════════════════════════════════════
echo.

:: Abrir Chrome en segundo plano (esperando 3 segundos para que Streamlit inicie)
start "" cmd /c "timeout /t 3 /nobreak >nul && start chrome http://localhost:8501"

:: Ejecutar Streamlit (sin navegador propio porque ya abrimos Chrome)
streamlit run Inicio.py --server.port 8501 --server.headless true --server.address localhost ^
    --browser.gatherUsageStats false

:: Si Streamlit termina, pausar para ver mensajes de error
echo.
echo ══════════════════════════════════════════════════════════════
echo   La aplicación se ha detenido.
echo ══════════════════════════════════════════════════════════════
pause
