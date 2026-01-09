' ============================================
' SGTE - Lanzador Principal
' Ejecuta el servidor sin mostrar ventanas
' ============================================
' Este es el archivo principal - Haz doble clic aquí para iniciar SGTE

Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

' Obtener el directorio del script
scriptPath = fso.GetParentFolderName(WScript.ScriptFullName)

' Verificar si existe el entorno virtual
pythonExe = scriptPath & "\venv\Scripts\python.exe"

' Si no existe en venv, usar Python del sistema
If Not fso.FileExists(pythonExe) Then
    pythonToUse = "python.exe"
Else
    pythonToUse = pythonExe
End If

scriptFile = scriptPath & "\iniciar_servidor.py"

' Verificar que el archivo Python existe
If Not fso.FileExists(scriptFile) Then
    MsgBox "Error: No se encontró el archivo iniciar_servidor.py" & vbCrLf & vbCrLf & "Asegúrate de estar en el directorio correcto del proyecto.", vbCritical, "SGTE - Error"
    WScript.Quit
End If

' Ejecutar el script Python sin mostrar ventana (0 = oculto)
WshShell.Run """" & pythonToUse & """ """ & scriptFile & """", 0, False

' El script Python se encarga de abrir el navegador cuando el servidor esté listo
' No mostrar ningún mensaje, ejecutar completamente en segundo plano
