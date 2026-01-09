"""API Routes para dashboard y métricas."""
from fastapi import APIRouter, HTTPException
from typing import Dict, List
from datetime import datetime
import sys
from pathlib import Path

# Agregar el directorio raíz al path
ROOT_DIR = Path(__file__).parent.parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from database import get_session_context, Estudiante, Proyecto, Expediente, EstadoExpediente
from sqlalchemy import func

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/metricas")
async def obtener_metricas():
    """Obtiene métricas generales del sistema para el dashboard."""
    try:
        with get_session_context() as session:
            total_estudiantes = session.query(func.count(Estudiante.run)).scalar() or 0
            total_proyectos = session.query(func.count(Proyecto.id)).scalar() or 0
            
            # Contar por estado de expediente
            pendientes = session.query(func.count(Expediente.id)).filter(
                Expediente.estado == EstadoExpediente.PENDIENTE
            ).scalar() or 0
            
            en_proceso = session.query(func.count(Expediente.id)).filter(
                Expediente.estado == EstadoExpediente.EN_PROCESO
            ).scalar() or 0
            
            listos = session.query(func.count(Expediente.id)).filter(
                Expediente.estado == EstadoExpediente.LISTO_ENVIO
            ).scalar() or 0
            
            enviados = session.query(func.count(Expediente.id)).filter(
                Expediente.estado == EstadoExpediente.ENVIADO
            ).scalar() or 0
            
            titulados = session.query(func.count(Expediente.id)).filter(
                Expediente.titulado == True
            ).scalar() or 0
            
            return {
                "success": True,
                "data": {
                    "total_estudiantes": total_estudiantes,
                    "total_proyectos": total_proyectos,
                    "pendientes": pendientes,
                    "en_proceso": en_proceso,
                    "listos": listos,
                    "enviados": enviados,
                    "titulados": titulados
                }
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/distribucion-carreras")
async def obtener_distribucion_carreras():
    """Obtiene distribución de estudiantes por carrera."""
    try:
        with get_session_context() as session:
            resultado = session.query(
                Estudiante.carrera,
                func.count(Estudiante.run).label('cantidad')
            ).group_by(Estudiante.carrera).all()
            
            return {
                "success": True,
                "data": [{"carrera": r.carrera, "cantidad": r.cantidad} for r in resultado]
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ultimos-registros")
async def obtener_ultimos_registros(limit: int = 10):
    """Obtiene los últimos estudiantes registrados."""
    try:
        with get_session_context() as session:
            estudiantes = session.query(Estudiante).order_by(
                Estudiante.created_at.desc()
            ).limit(limit).all()
            
            return {
                "success": True,
                "data": [{
                    "run": e.run,
                    "nombre_completo": e.nombre_completo,
                    "carrera": e.carrera,
                    "registrado": e.created_at.strftime("%d/%m/%Y %H:%M") if e.created_at else "-"
                } for e in estudiantes]
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
