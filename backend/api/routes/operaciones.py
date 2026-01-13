"""API Routes para operaciones masivas."""
from fastapi import APIRouter, HTTPException, UploadFile, File, Query
from fastapi.responses import StreamingResponse
from typing import List, Optional
from pydantic import BaseModel
from io import BytesIO
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from services.memo_generator import generar_memorandums_masivo
from services.email_queue import verificar_outlook, enviar_correos_masivo
from services.estudiantes import buscar_estudiantes, contar_estudiantes_filtrados, obtener_carreras
from services.sync_excel import sincronizar_excel
from services.pdf_splitter_optimized import procesar_pdf_masivo, verificar_pymupdf_disponible
from database import get_session_context, Expediente, EstadoExpediente
from datetime import datetime

router = APIRouter(prefix="/api/operaciones", tags=["operaciones"])


class OperacionMasivaRequest(BaseModel):
    runs: List[str]
    solo_borrador: bool = True  # Para correos


@router.get("/estudiantes")
async def obtener_estudiantes_paginados(
    pagina: int = Query(1, ge=1, description="Número de página"),
    filas_por_pagina: int = Query(20, ge=1, le=100, description="Filas por página"),
    termino: Optional[str] = Query(None, description="Búsqueda por RUN o nombre"),
    carrera: Optional[str] = Query(None, description="Filtrar por carrera")
):
    """
    Obtiene estudiantes paginados para la tabla de operaciones masivas.
    """
    try:
        # Calcular offset
        offset = (pagina - 1) * filas_por_pagina
        
        # Obtener estudiantes
        estudiantes = buscar_estudiantes(
            termino=termino,
            carrera=carrera,
            limite=filas_por_pagina,
            offset=offset
        )
        
        # Contar total
        total = contar_estudiantes_filtrados(termino=termino, carrera=carrera)
        
        # Calcular total de páginas
        total_paginas = (total + filas_por_pagina - 1) // filas_por_pagina if total > 0 else 1
        
        return {
            "success": True,
            "data": {
                "estudiantes": estudiantes,
                "paginacion": {
                    "pagina_actual": pagina,
                    "filas_por_pagina": filas_por_pagina,
                    "total_registros": total,
                    "total_paginas": total_paginas,
                    "tiene_anterior": pagina > 1,
                    "tiene_siguiente": pagina < total_paginas
                }
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/carreras")
async def obtener_carreras_endpoint():
    """Obtiene lista de carreras para el filtro."""
    try:
        carreras = obtener_carreras()
        return {
            "success": True,
            "data": carreras
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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


@router.post("/sincronizar-excel")
async def sincronizar_excel_endpoint():
    """
    Sincroniza datos desde el archivo Excel histórico de Google Drive.
    Lee el archivo 'G:\\Mi unidad\\SGTE\\alumnos.xlsx' e importa/actualiza
    estudiantes, proyectos, comisiones y expedientes en la base de datos.
    
    Procesa las siguientes hojas:
    - 2025-2, 2025-1, 2024-2, 2024-1
    - Carga Consolidada 2025-2, Carga Consolidada 2025-1
    - Carga Consolidada 2024-2, Carga Consolidada 2024-1
    """
    try:
        # Ejecutar sincronización
        resultado = sincronizar_excel(usuario="Sistema")
        
        # Formatear respuesta
        mensaje = (
            f"Sincronización completada: {resultado['hojas_procesadas']} hojas procesadas, "
            f"{resultado['procesadas']} filas procesadas, {resultado['errores']} errores "
            f"de {resultado['total_filas']} filas totales"
        )
        
        return {
            "success": resultado["success"],
            "data": {
                "total_filas": resultado["total_filas"],
                "procesadas": resultado["procesadas"],
                "errores": resultado["errores"],
                "hojas_procesadas": resultado.get("hojas_procesadas", 0),
                "mensaje": mensaje,
                "detalles": resultado.get("detalles", {})
            }
        }
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=404,
            detail=f"Archivo Excel no encontrado. Verifica que exista en: G:\\Mi unidad\\SGTE\\alumnos.xlsx - {str(e)}"
        )
    except Exception as e:
        import traceback
        error_detail = f"Error en sincronización: {str(e)}\n\nTraceback:\n{traceback.format_exc()}"
        raise HTTPException(status_code=500, detail=error_detail)


@router.get("/verificar-pdf-splitter")
async def verificar_pdf_splitter():
    """Verifica si las dependencias de PDF Splitter están disponibles."""
    disponible = verificar_pymupdf_disponible()
    return {
        "success": True,
        "disponible": disponible,
        "mensaje": "PyMuPDF disponible" if disponible else "PyMuPDF no está instalado"
    }


@router.post("/procesar-pdf")
async def procesar_pdf(pdf: UploadFile = File(...)):
    """Procesa un PDF masivo y lo divide por estudiante."""
    try:
        # Verificar que es PDF
        if not pdf.filename or not pdf.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Solo se aceptan archivos PDF")
        
        # Verificar dependencias
        if not verificar_pymupdf_disponible():
            raise HTTPException(
                status_code=500,
                detail="PyMuPDF no está instalado. Ejecute: pip install pymupdf"
            )
        
        # Leer contenido del PDF
        contenido = await pdf.read()
        
        # Verificar tamaño (200 MB máximo)
        if len(contenido) > 200 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="El archivo es demasiado grande (máximo 200 MB)")
        
        # Procesar PDF
        resultado = procesar_pdf_masivo(contenido, callback=None)
        
        # Agrupar por estudiante para el resumen
        estudiantes_dict = {}
        for detalle in resultado.detalles:
            if detalle.asignado and detalle.run_detectado:
                run = detalle.run_detectado
                if run not in estudiantes_dict:
                    estudiantes_dict[run] = {
                        "run": run,
                        "paginas": [],
                        "archivo": detalle.ruta_guardado
                    }
                estudiantes_dict[run]["paginas"].append(detalle.pagina)
        
        return {
            "success": True,
            "data": {
                "total_paginas": resultado.total_paginas,
                "paginas_asignadas": resultado.paginas_asignadas,
                "paginas_sin_asignar": resultado.paginas_sin_asignar,
                "errores": resultado.errores,
                "tiempo_proceso": resultado.tiempo_proceso,
                "estudiantes_encontrados": len(estudiantes_dict),
                "resumen": list(estudiantes_dict.values())
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
