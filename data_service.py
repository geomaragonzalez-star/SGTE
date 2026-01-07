from pathlib import Path
import pandas as pd
from PySide6.QtCore import QSettings
from typing import Optional
from datetime import datetime

SETTINGS_ORG = "SIGETI"
SETTINGS_APP = "SIGETI"
SETTINGS_KEY_EXCEL = "data/excel_path"

DEFAULT_DRIVE_EXCEL = Path(r"G:/Mi unidad/SIGETI/alumnos.xlsx")

# Esquema canónico de columnas
CANON_COLS = [
    "nombre_completo", "rut", "carrera", "modalidad", "semestre",
    "titulo_proyecto", "profesor_guia", "corrector1", "corrector2",
    "fecha_examen", "sala", "estado_constancias"
]

def get_excel_path() -> Optional[Path]:
    s = QSettings(SETTINGS_ORG, SETTINGS_APP)
    p = s.value(SETTINGS_KEY_EXCEL, type=str)
    if p:
        return Path(p)
    if DEFAULT_DRIVE_EXCEL.exists():
        set_excel_path(DEFAULT_DRIVE_EXCEL)
        return DEFAULT_DRIVE_EXCEL
    return None

def set_excel_path(p: Path) -> None:
    s = QSettings(SETTINGS_ORG, SETTINGS_APP)
    s.setValue(SETTINGS_KEY_EXCEL, str(p))

def get_drive_root_dir() -> Path:
    """Devuelve la CARPETA donde vive el Excel de alumnos (Google Drive local)."""
    excel = get_excel_path()
    if not excel or not excel.exists():
        raise FileNotFoundError("No hay ruta Excel configurada o el archivo no existe.")
    return excel.parent

def get_students_base_dir() -> Path:
    """Devuelve y crea si falta la carpeta base 'Estudiantes' en el mismo Drive."""
    base = get_drive_root_dir() / "Estudiantes"
    base.mkdir(parents=True, exist_ok=True)
    return base

def load_students_df(semester: Optional[str] = None) -> pd.DataFrame:
    """
    Carga estudiantes desde Excel y normaliza columnas a esquema canónico.
    Retorna DataFrame con todas las columnas de CANON_COLS (vacías si no existen).
    """
    excel_path = get_excel_path()
    if not excel_path or not excel_path.exists():
        raise FileNotFoundError("No hay ruta Excel configurada o el archivo no existe.")
    
    xls = pd.ExcelFile(excel_path, engine="openpyxl")
    sheet = semester if (semester and semester in xls.sheet_names) else xls.sheet_names[0]
    df = pd.read_excel(xls, sheet_name=sheet)

    # Mapeo flexible de nombres de columnas
    rename_map = {
        "RUT": "rut", "Rut": "rut", "RUT ": "rut",
        "Nombre": "nombre", "Apellido": "apellido",
        "Carrera": "carrera", "Modalidad": "modalidad",
        "Semestre": "semestre",
        "Título Proyecto": "titulo_proyecto", "Titulo Proyecto": "titulo_proyecto",
        "Profesor Guía": "profesor_guia", "Profesor Guia": "profesor_guia",
        "Corrector 1": "corrector1", "Corrector1": "corrector1",
        "Corrector 2": "corrector2", "Corrector2": "corrector2",
        "Fecha Examen": "fecha_examen", "Fecha examen": "fecha_examen", "Fecha_Examen": "fecha_examen",
        "Sala": "sala",
        "Estado Constancias": "estado_constancias", "Estado_Constancias": "estado_constancias",
    }
    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})
    
    # Construir nombre_completo si no existe
    if "nombre_completo" not in df.columns:
        if "nombre" in df.columns and "apellido" in df.columns:
            df["nombre_completo"] = (df["nombre"].astype(str) + " " + df["apellido"].astype(str)).str.strip()
        elif "nombre" in df.columns:
            df["nombre_completo"] = df["nombre"].astype(str).str.strip()
        else:
            df["nombre_completo"] = ""
    
    # Asegurar todas las columnas canónicas existen (vacías si faltan)
    for col in CANON_COLS:
        if col not in df.columns:
            df[col] = ""
    
    # Parsear fecha_examen si existe y está en formato texto
    if "fecha_examen" in df.columns:
        try:
            df["fecha_examen"] = pd.to_datetime(df["fecha_examen"], errors='coerce')
        except Exception:
            pass  # Dejar como está si falla
    
    # Limpiar valores vacíos (reemplazar NaN/None con strings vacíos donde sea aplicable)
    for col in CANON_COLS:
        if df[col].dtype == 'object':
            df[col] = df[col].fillna("").astype(str).str.strip()
    
    return df[CANON_COLS]  # Retornar solo columnas canónicas en orden
