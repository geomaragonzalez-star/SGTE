# services/excel_export.py
"""
Exportación a Excel (RF-06, HU-05).
Respaldo de datos en formato compatible con planillas históricas.
"""

import io
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
import pandas as pd
from loguru import logger

from config import get_config
from database import (
    get_session_context, 
    Estudiante, 
    Proyecto, 
    Comision, 
    Expediente, 
    Documento,
    Hito
)
from database.connection import log_user_action


# ============================================
# MAPEO DE COLUMNAS INSTITUCIONAL
# ============================================

COLUMN_MAPPING = {
    "run": "R.U.N",
    "nombres": "NOMBRES",
    "apellidos": "APELLIDOS",
    "carrera": "CARRERA",
    "email": "EMAIL",
    "semestre": "SEMESTRE",
    "modalidad": "MODALIDAD",
    "titulo": "TITULO PROYECTO",
    "profesor_guia": "PROFESOR GUIA",
    "corrector_1": "CORRECTOR 1",
    "corrector_2": "CORRECTOR 2",
    "estado": "ESTADO",
    "observaciones": "OBSERVACIONES",
    "titulado": "TITULADO",
    "fecha_registro": "FECHA REGISTRO",
}


# ============================================
# FUNCIONES DE EXPORTACIÓN
# ============================================

def obtener_datos_completos() -> pd.DataFrame:
    """
    Obtiene todos los datos del sistema en formato DataFrame.
    Realiza joins entre todas las tablas principales.
    """
    try:
        with get_session_context() as session:
            # Query con todos los joins
            query = session.query(
                Estudiante.run,
                Estudiante.nombres,
                Estudiante.apellidos,
                Estudiante.carrera,
                Estudiante.email,
                Estudiante.created_at.label('fecha_registro'),
                Proyecto.semestre,
                Proyecto.modalidad,
                Proyecto.titulo,
                Comision.profesor_guia,
                Comision.corrector_1,
                Comision.corrector_2,
                Expediente.estado,
                Expediente.observaciones,
                Expediente.titulado,
                Expediente.fecha_envio,
                Expediente.semestre_titulacion
            ).outerjoin(
                Proyecto, Proyecto.estudiante_run == Estudiante.run
            ).outerjoin(
                Comision, Comision.proyecto_id == Proyecto.id
            ).outerjoin(
                Expediente, Expediente.proyecto_id == Proyecto.id
            )
            
            resultados = query.all()
            
            # Convertir a DataFrame
            data = []
            for r in resultados:
                data.append({
                    "run": r.run,
                    "nombres": r.nombres,
                    "apellidos": r.apellidos,
                    "carrera": r.carrera,
                    "email": r.email or "",
                    "fecha_registro": r.fecha_registro.strftime("%d/%m/%Y") if r.fecha_registro else "",
                    "semestre": r.semestre or "",
                    "modalidad": r.modalidad.value if r.modalidad else "",
                    "titulo": r.titulo or "",
                    "profesor_guia": r.profesor_guia or "",
                    "corrector_1": r.corrector_1 or "",
                    "corrector_2": r.corrector_2 or "",
                    "estado": r.estado.value if r.estado else "sin_expediente",
                    "observaciones": r.observaciones or "",
                    "titulado": "SI" if r.titulado else "NO",
                })
            
            df = pd.DataFrame(data)
            
            # Renombrar columnas al formato institucional
            df = df.rename(columns=COLUMN_MAPPING)
            
            return df
            
    except Exception as e:
        logger.error(f"Error obteniendo datos: {e}")
        return pd.DataFrame()


def generar_reporte_maestro() -> tuple[bytes, str, int]:
    """
    Genera el reporte maestro en formato Excel.
    
    Returns:
        Tuple: (bytes_excel, nombre_archivo, cantidad_registros)
    """
    try:
        df = obtener_datos_completos()
        
        if df.empty:
            logger.warning("No hay datos para exportar")
            return b"", "", 0
        
        # Crear Excel con formato
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Reporte Maestro')
            
            # Ajustar ancho de columnas
            worksheet = writer.sheets['Reporte Maestro']
            for idx, col in enumerate(df.columns):
                max_length = max(
                    df[col].astype(str).apply(len).max(),
                    len(col)
                ) + 2
                worksheet.column_dimensions[chr(65 + idx)].width = min(max_length, 50)
        
        output.seek(0)
        
        # Nombre del archivo
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        nombre = f"Reporte_Maestro_SGTE_{timestamp}.xlsx"
        
        # Registrar en bitácora
        log_user_action(
            tabla="exports",
            registro_id="reporte_maestro",
            accion="EXPORT",
            descripcion=f"Reporte maestro generado: {len(df)} registros"
        )
        
        logger.info(f"Reporte maestro generado: {nombre} ({len(df)} registros)")
        
        return output.getvalue(), nombre, len(df)
        
    except Exception as e:
        logger.error(f"Error generando reporte: {e}")
        return b"", "", 0


def guardar_backup_automatico() -> Optional[Path]:
    """
    Guarda un backup automático en la carpeta de respaldos.
    
    Returns:
        Path del archivo guardado o None si falla
    """
    try:
        config = get_config()
        backup_dir = Path(config.paths.backup_path)
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        excel_bytes, nombre, registros = generar_reporte_maestro()
        
        if not excel_bytes:
            return None
        
        ruta = backup_dir / nombre
        
        with open(ruta, 'wb') as f:
            f.write(excel_bytes)
        
        logger.info(f"Backup guardado: {ruta}")
        return ruta
        
    except Exception as e:
        logger.error(f"Error guardando backup: {e}")
        return None


def exportar_estudiantes() -> tuple[bytes, str, int]:
    """Exporta solo la tabla de estudiantes."""
    try:
        with get_session_context() as session:
            estudiantes = session.query(Estudiante).all()
            
            data = [{
                "R.U.N": e.run,
                "NOMBRES": e.nombres,
                "APELLIDOS": e.apellidos,
                "CARRERA": e.carrera,
                "EMAIL": e.email or "",
                "FECHA REGISTRO": e.created_at.strftime("%d/%m/%Y") if e.created_at else ""
            } for e in estudiantes]
            
            df = pd.DataFrame(data)
            
            output = io.BytesIO()
            df.to_excel(output, index=False, engine='openpyxl')
            output.seek(0)
            
            nombre = f"Estudiantes_{datetime.now().strftime('%Y%m%d')}.xlsx"
            
            return output.getvalue(), nombre, len(df)
            
    except Exception as e:
        logger.error(f"Error exportando estudiantes: {e}")
        return b"", "", 0


def exportar_por_estado(estado: str) -> tuple[bytes, str, int]:
    """Exporta estudiantes filtrados por estado de expediente."""
    try:
        df = obtener_datos_completos()
        
        if 'ESTADO' in df.columns:
            df_filtrado = df[df['ESTADO'] == estado]
        else:
            df_filtrado = df
        
        output = io.BytesIO()
        df_filtrado.to_excel(output, index=False, engine='openpyxl')
        output.seek(0)
        
        nombre = f"Reporte_{estado}_{datetime.now().strftime('%Y%m%d')}.xlsx"
        
        return output.getvalue(), nombre, len(df_filtrado)
        
    except Exception as e:
        logger.error(f"Error exportando por estado: {e}")
        return b"", "", 0
