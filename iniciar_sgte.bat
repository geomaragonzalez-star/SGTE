@echo off
REM Lanzador para SGTE - Sin mostrar ventana de CMD
cd /d %~dp0
REM Usar PowerShell para ejecutar el VBS sin mostrar ventana
powershell.exe -WindowStyle Hidden -Command "Start-Process -FilePath 'wscript.exe' -ArgumentList '//nologo iniciar_sgte.vbs' -WindowStyle Hidden"
exit
