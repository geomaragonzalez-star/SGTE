"""API Routes para gestión de expedientes."""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel
import sys
from pathlib import Path

# Agregar el directorio raíz al path
ROOT_DIR = Path(__file__).parent.parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from database import get_session_context, Expediente, Proyecto, Estudiante, EstadoExpediente
from sqlalchemy import func

router = APIRouter(prefix="/api/expedientes", tags=["expedientes"])


class ExpedienteUpdate(BaseModel):
    estado: Optional[str] = None
    observaciones: Optional[str] = None
    titulado: Optional[bool] = None


@router.get("/")
async def listar_expedientes(
    estado: Optional[str] = Query(None),
    estudiante_run: Optional[str] = Query(None)
):
    """Lista expedientes con filtros opcionales."""
    try:
        with get_session_context() as session:
            query = session.query(Expediente).join(Proyecto)
            
            if estado:
                try:
                    estado_enum = EstadoExpediente(estado)
                    query = query.filter(Expediente.estado == estado_enum)
                except ValueError:
                    pass
            
            if estudiante_run:
                query = query.filter(Proyecto.estudiante_run == estudiante_run)
            
            expedientes = query.all()
            
            return {
                "success": True,
                "data": [{
                    "id": e.id,
                    "proyecto_id": e.proyecto_id,
                    "estado": e.estado.value if e.estado else None,
                    "observaciones": e.observaciones,
                    "fecha_envio": e.fecha_envio.isoformat() if e.fecha_envio else None,
                    "fecha_aprobacion": e.fecha_aprobacion.isoformat() if e.fecha_aprobacion else None,
                    "titulado": e.titulado,
                    "semestre_titulacion": e.semestre_titulacion
                } for e in expedientes],
                "count": len(expedientes)
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/estadisticas")
async def obtener_estadisticas_expedientes():
    """Obtiene estadísticas de expedientes por estado."""
    try:
        with get_session_context() as session:
            stats = {}
            for estado in EstadoExpediente:
                count = session.query(func.count(Expediente.id)).filter(
                    Expediente.estado == estado
                ).scalar() or 0
                stats[estado.value] = count
            
            titulados = session.query(func.count(Expediente.id)).filter(
                Expediente.titulado == True
            ).scalar() or 0
            
            return {
                "success": True,
                "data": {
                    "por_estado": stats,
                    "titulados": titulados,
                    "total": sum(stats.values())
                }
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{expediente_id}")
async def actualizar_expediente(expediente_id: int, update: ExpedienteUpdate):
    """Actualiza un expediente."""
    try:
        with get_session_context() as session:
            expediente = session.query(Expediente).filter(
                Expediente.id == expediente_id
            ).first()
            
            if not expediente:
                raise HTTPException(status_code=404, detail="Expediente no encontrado")
            
            if update.estado:
                try:
                    expediente.estado = EstadoExpediente(update.estado)
                except ValueError:
                    raise HTTPException(status_code=400, detail="Estado inválido")
            
            if update.observaciones is not None:
                expediente.observaciones = update.observaciones
            
            if update.titulado is not None:
                expediente.titulado = update.titulado
            
            expediente.updated_at = datetime.now()
            session.commit()
            
            return {
                "success": True,
                "message": "Expediente actualizado",
                "data": {
                    "id": expediente.id,
                    "estado": expediente.estado.value,
                    "titulado": expediente.titulado
                }
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
