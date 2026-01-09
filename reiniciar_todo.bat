@echo off
echo ===================================================
echo   REINICIANDO SISTEMA SGTE - LIMPIEZA TOTAL
echo ===================================================

echo.
echo 1. Deteniendo procesos antiguos...
taskkill /F /IM python.exe >nul 2>&1
taskkill /F /IM streamlit.exe >nul 2>&1

echo.
echo 2. Esperando liberacion de puertos...
timeout /t 2 /nobreak >nul

echo.
echo 3. Iniciando nuevo sistema (Inicio.py)...
echo.

call run.bat
