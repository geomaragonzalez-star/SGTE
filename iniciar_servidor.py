"""
Script Python para iniciar el servidor FastAPI en segundo plano
y abrir el navegador automáticamente.
"""
import subprocess
import sys
import time
import webbrowser
from pathlib import Path
import os
import socket
import urllib.request

# Flag para ocultar ventana en Windows
CREATE_NO_WINDOW = 0x08000000 if sys.platform == "win32" else 0

def is_port_open(host, port, timeout=1):
    """Verifica si un puerto está abierto."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except:
        return False

def is_server_ready(url, max_attempts=30, delay=0.5):
    """Verifica si el servidor está listo haciendo peticiones HTTP."""
    for _ in range(max_attempts):
        try:
            response = urllib.request.urlopen(url, timeout=2)
            if response.getcode() == 200:
                return True
        except:
            pass
        time.sleep(delay)
    return False

def main():
    # Cambiar al directorio raíz del proyecto
    root_dir = Path(__file__).parent
    os.chdir(root_dir)
    
    # Activar entorno virtual si existe
    venv_python = root_dir / "venv" / "Scripts" / "python.exe"
    if venv_python.exists():
        python_exe = str(venv_python)
    else:
        python_exe = sys.executable
    
    # Verificar dependencias (solo si es necesario, no cada vez)
    try:
        import fastapi
        import uvicorn
        import jinja2
    except ImportError:
        subprocess.run(
            [python_exe, "-m", "pip", "install", "-q", "-r", "requirements_backend.txt"], 
            cwd=root_dir,
            creationflags=CREATE_NO_WINDOW,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
    
    # Iniciar servidor en segundo plano
    server_process = subprocess.Popen(
        [python_exe, "-m", "uvicorn", "backend.api.main:app", 
         "--reload", "--host", "127.0.0.1", "--port", "8000"],
        cwd=root_dir,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=CREATE_NO_WINDOW
    )
    
    # Esperar a que el servidor esté listo (verificación inteligente)
    # Primero esperamos que el puerto esté abierto
    max_wait = 15  # máximo 15 segundos
    waited = 0
    while not is_port_open("127.0.0.1", 8000) and waited < max_wait:
        time.sleep(0.3)
        waited += 0.3
    
    # Luego verificamos que el servidor responda HTTP
    if is_server_ready("http://127.0.0.1:8000/", max_attempts=10, delay=0.3):
        # Abrir navegador solo cuando el servidor esté listo
        try:
            webbrowser.open("http://localhost:8000")
        except:
            pass
    else:
        # Si no responde, abrir de todas formas después de un tiempo
        time.sleep(1)
        try:
            webbrowser.open("http://localhost:8000")
        except:
            pass
    
    # Mantener el script corriendo para que el servidor siga activo
    try:
        server_process.wait()
    except KeyboardInterrupt:
        server_process.terminate()

if __name__ == "__main__":
    main()
