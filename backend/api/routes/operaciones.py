"""API Routes para operaciones masivas."""
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from typing import List
from pydantic import BaseModel
from io import BytesIO
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from services.memo_generator import generar_memorandums_masivo
from services.email_queue import verificar_outlook, enviar_correos_masivo
from services.estudiantes import buscar_estudiantes
from database import get_session_context, Expediente, EstadoExpediente
from datetime import datetime

router = APIRouter(prefix="/api/operaciones", tags=["operaciones"])


class OperacionMasivaRequest(BaseModel):
    runs: List[str]
    solo_borrador: bool = True  # Para correos


@router.post("/generar-memos")
async def generar_memos_masivo(request: OperacionMasivaRequest):
    """Genera memorándums masivos para los estudiantes seleccionados."""
    try:
        if not request.runs:
            raise HTTPException(status_code=400, detail="Debe seleccionar al menos un estudiante")
        
        # Generar memorándums
        zip_bytes, resultados_list = generar_memorandums_masivo(
            request.runs,
            numero_memo_inicio=1,
            callback=None
        )
        
        exitosos = sum(1 for r in resultados_list if r.exito)
        fallidos = len(resultados_list) - exitosos
        
        # Si no se generó ningún memorándum, devolver error con detalles
        if exitosos == 0:
            errores = [f"{r.run}: {r.error}" for r in resultados_list if r.error]
            mensaje = f"No se pudo generar ningún memorándum. Errores: {'; '.join(errores[:5])}"
            if len(errores) > 5:
                mensaje += f" ... y {len(errores) - 5} más"
            raise HTTPException(status_code=400, detail=mensaje)
        
        filename = f"memorandums_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
        
        return StreamingResponse(
            BytesIO(zip_bytes),
            media_type="application/zip",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "X-Exitosos": str(exitosos),
                "X-Fallidos": str(fallidos),
                "X-Total": str(len(request.runs))
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_detail = f"{str(e)}\n\nTraceback:\n{traceback.format_exc()}"
        raise HTTPException(status_code=500, detail=error_detail)


@router.post("/enviar-correos")
async def enviar_correos_masivo_endpoint(request: OperacionMasivaRequest):
    """Envía correos masivos a Registro Curricular."""
    try:
        if not request.runs:
            raise HTTPException(status_code=400, detail="Debe seleccionar al menos un estudiante")
        
        # Verificar Outlook
        outlook_ok, outlook_msg = verificar_outlook()
        if not outlook_ok:
            raise HTTPException(status_code=400, detail=f"Outlook no disponible: {outlook_msg}")
        
        # Enviar correos
        resultado = enviar_correos_masivo(
            request.runs,
            callback=None,
            solo_borrador=request.solo_borrador
        )
        
        return {
            "success": True,
            "data": {
                "exitosos": resultado.exitosos,
                "fallidos": resultado.fallidos,
                "interrumpido": resultado.interrumpido,
                "resultados": [
                    {
                        "run": r.run,
                        "exito": r.exito,
                        "mensaje": r.mensaje
                    }
                    for r in resultado.resultados
                ]
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cambiar-estado")
async def cambiar_estado_masivo(request: OperacionMasivaRequest, estado: str):
    """Cambia el estado de expedientes masivamente."""
    try:
        if not request.runs:
            raise HTTPException(status_code=400, detail="Debe seleccionar al menos un estudiante")
        
        try:
            estado_enum = EstadoExpediente(estado)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Estado inválido: {estado}")
        
        with get_session_context() as session:
            actualizados = 0
            for run in request.runs:
                # Buscar expediente del estudiante
                from database import Proyecto
                proyecto = session.query(Proyecto).filter(
                    Proyecto.estudiante_run == run
                ).first()
                
                if proyecto:
                    expediente = session.query(Expediente).filter(
                        Expediente.proyecto_id == proyecto.id
                    ).first()
                    
                    if expediente:
                        expediente.estado = estado_enum
                        actualizados += 1
            
            session.commit()
        
        return {
            "success": True,
            "message": f"Estado actualizado para {actualizados} expedientes",
            "actualizados": actualizados
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/verificar-outlook")
async def verificar_outlook_endpoint():
    """Verifica si Outlook está disponible."""
    try:
        disponible, mensaje = verificar_outlook()
        return {
            "success": disponible,
            "disponible": disponible,
            "mensaje": mensaje
        }
    except Exception as e:
        return {
            "success": False,
            "disponible": False,
            "mensaje": str(e)
        }
