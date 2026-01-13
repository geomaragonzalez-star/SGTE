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
    """Genera memorándum para un estudiante y descarga Word directamente (sin ZIP)."""
    try:
        if not request.runs or len(request.runs) == 0:
            raise HTTPException(status_code=400, detail="Debe seleccionar al menos un estudiante")
        
        # Siempre trabajar con el primer estudiante (el frontend maneja múltiples llamadas)
        from services.memo_generator import generar_memorandum
        
        run = request.runs[0]
        
        # Generar número de memo (001, 002, etc.)
        numero_memo = "001"
        if len(request.runs) > 1:
            # Si hay más de uno, el frontend debe pasar el índice
            numero_memo = str(len(request.runs)).zfill(3)
        
        exito, doc_bytes, nombre_archivo = generar_memorandum(run, numero_memo=numero_memo)
        
        if not exito:
            raise HTTPException(status_code=400, detail=f"Error generando memorándum para {run}: {nombre_archivo}")
        
        if not doc_bytes:
            raise HTTPException(status_code=500, detail=f"El documento generado está vacío para {run}")
        
        # Asegurar que el nombre del archivo termine en .docx
        if not nombre_archivo.lower().endswith('.docx'):
            nombre_archivo = nombre_archivo.rsplit('.', 1)[0] + '.docx'
        
        # Codificar el nombre del archivo para Content-Disposition (RFC 5987)
        import urllib.parse
        nombre_archivo_encoded = urllib.parse.quote(nombre_archivo.encode('utf-8'))
        
        # Crear respuesta con tipo MIME correcto para Word
        headers = {
            "Content-Disposition": f'attachment; filename="{nombre_archivo}"; filename*=UTF-8\'\'{nombre_archivo_encoded}',
            "Content-Type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "Content-Length": str(len(doc_bytes)),
            "X-Content-Type-Options": "nosniff"  # Evitar que el navegador detecte el tipo automáticamente
        }
        
        return StreamingResponse(
            BytesIO(doc_bytes),
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers=headers
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
