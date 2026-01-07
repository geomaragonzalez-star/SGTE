from pathlib import Path
import os
import json
from typing import Optional

def get_onedrive_students_base() -> Path:
    """
    Determina la carpeta base para estudiantes, priorizando OneDrive.
    
    Returns:
        Path: Ruta a la carpeta base de estudiantes
    """
    # 1. Verificar configuración guardada
    config_path = Path(__file__).parent / "config.json"
    if config_path.exists():
        try:
            with open(config_path, "r") as f:
                config = json.load(f)
                if "students_base_dir" in config:
                    base_dir = Path(config["students_base_dir"])
                    print(f"[INFO] Usando ruta configurada: {base_dir}")
                    base_dir.mkdir(parents=True, exist_ok=True)
                    return base_dir
        except Exception as e:
            print(f"[WARN] Error leyendo config.json: {e}")
    
    # 2. Verificar variable de entorno
    env_dir = os.environ.get("TESIS_STUDENTS_DIR")
    if env_dir:
        base_dir = Path(env_dir).expanduser()
        print(f"[INFO] Usando ruta desde TESIS_STUDENTS_DIR: {base_dir}")
        base_dir.mkdir(parents=True, exist_ok=True)
        return base_dir
    
    # 3. Detectar OneDrive
    # Primero OneDrive Comercial (institucional)
    onedrive_com = os.environ.get("OneDriveCommercial")
    if onedrive_com:
        base_dir = Path(onedrive_com) / "USACH" / "Estudiantes"
        print(f"[INFO] Usando OneDrive Comercial: {base_dir}")
        base_dir.mkdir(parents=True, exist_ok=True)
        return base_dir
        
    # Luego OneDrive Personal
    onedrive = os.environ.get("OneDrive")
    if onedrive:
        base_dir = Path(onedrive) / "USACH" / "Estudiantes"
        print(f"[INFO] Usando OneDrive Personal: {base_dir}")
        base_dir.mkdir(parents=True, exist_ok=True)
        return base_dir
    
    # 4. Fallback: Usar directorio del script
    base_dir = Path(__file__).parent / "Estudiantes"
    print(f"[WARN] No se encontró OneDrive. Usando directorio local: {base_dir}")
    base_dir.mkdir(parents=True, exist_ok=True)
    return base_dir

def save_base_dir_config(path: Path) -> None:
    """Guarda la ruta base configurada por el usuario"""
    config_path = Path(__file__).parent / "config.json"
    config = {"students_base_dir": str(path)}
    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)
