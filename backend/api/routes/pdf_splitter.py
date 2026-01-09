"""API Routes para PDF Splitter."""
from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from typing import Optional
import sys
from pathlib import Path
from io import BytesIO
from datetime import datetime

ROOT_DIR = Path(__file__).parent.parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from services.pdf_splitter_optimized import procesar_pdf_masivo, verificar_pymupdf_disponible

router = APIRouter(prefix="/api/pdf-splitter", tags=["pdf-splitter"])


@router.get("/verificar")
async def verificar_pdf_splitter():
    """Verifica si las dependencias de PDF Splitter están disponibles."""
    disponible = verificar_pymupdf_disponible()
    return {
        "success": True,
        "disponible": disponible,
        "mensaje": "PyMuPDF disponible" if disponible else "PyMuPDF no está instalado"
    }


@router.post("/procesar")
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
