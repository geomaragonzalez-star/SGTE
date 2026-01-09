' ============================================
' SGTE - Launcher Invisible
' ============================================
' Este script ejecuta run.bat sin mostrar la ventana de comandos
' Versión: 2.0
' Fecha: 2026-01-08
' ============================================

Option Explicit

Dim objShell, strBatPath, intWindowStyle

' Crear objeto Shell
Set objShell = CreateObject("WScript.Shell")

' Ruta absoluta al archivo run.bat
strBatPath = "C:\Users\YomiT\Documents\Tesis\SGTE\run.bat"

' WindowStyle = 0 (Ocultar ventana completamente)
' WindowStyle = 1 (Normal)
' WindowStyle = 2 (Minimizada)
' WindowStyle = 3 (Maximizada)
intWindowStyle = 0

' Ejecutar run.bat en modo invisible
' Parámetros: Command, WindowStyle, WaitOnReturn
objShell.Run """" & strBatPath & """", intWindowStyle, False

' Limpiar objeto
Set objShell = Nothing

' Mostrar notificación opcional (comentar si no deseas el mensaje)
' WScript.Echo "✓ SGTE iniciado en segundo plano" & vbCrLf & "Use 'detener_sistema.bat' para cerrar"
