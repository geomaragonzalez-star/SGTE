"""API Routes para gestión de estudiantes."""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List, Dict
from pydantic import BaseModel
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from services.estudiantes import (
    crear_estudiante,
    obtener_estudiante,
    buscar_estudiantes,
    listar_estudiantes,
    actualizar_estudiante,
    eliminar_estudiante,
    obtener_carreras,
    contar_estudiantes
)
from database import get_session_context, Estudiante, Documento, TipoDocumento

router = APIRouter(prefix="/api/estudiantes", tags=["estudiantes"])

# Documentos requeridos (mismo que en documentos.py)
DOCUMENTOS_REQUERIDOS = [
    TipoDocumento.BIENESTAR,
    TipoDocumento.FINANZAS_TITULO,
    TipoDocumento.FINANZAS_LICENCIA,
    TipoDocumento.BIBLIOTECA,
    TipoDocumento.SDT,
    TipoDocumento.MEMORANDUM
]


def verificar_estudiante_listo(run: str) -> bool:
    """Verifica si un estudiante tiene todos los documentos requeridos validados."""
    try:
        with get_session_context() as session:
            docs = session.query(Documento).filter(
                Documento.estudiante_run == run
            ).all()
            
            documentos_dict = {doc.tipo: doc for doc in docs}
            documentos_requeridos_validados = 0
            total_requeridos = len(DOCUMENTOS_REQUERIDOS) - 1  # -1 porque finanzas cuenta como uno
            
            for tipo_doc in DOCUMENTOS_REQUERIDOS:
                if tipo_doc == TipoDocumento.FINANZAS_TITULO:
                    validado_finanzas = (
                        (documentos_dict.get(TipoDocumento.FINANZAS_TITULO) and documentos_dict.get(TipoDocumento.FINANZAS_TITULO).validado) or
                        (documentos_dict.get(TipoDocumento.FINANZAS_LICENCIA) and documentos_dict.get(TipoDocumento.FINANZAS_LICENCIA).validado)
                    )
                    if validado_finanzas:
                        documentos_requeridos_validados += 1
                    continue
                elif tipo_doc == TipoDocumento.FINANZAS_LICENCIA:
                    continue
                
                doc = documentos_dict.get(tipo_doc)
                if doc and doc.validado:
                    documentos_requeridos_validados += 1
            
            return documentos_requeridos_validados == total_requeridos
    except:
        return False


@router.get("/checklist-status")
async def obtener_estado_checklist_masivo(runs: str = Query(..., description="Lista de RUNs separados por coma")):
    """Obtiene el estado del checklist para múltiples estudiantes."""
    try:
        runs_list = [r.strip() for r in runs.split(",") if r.strip()]
        resultado = {}
        
        for run in runs_list:
            resultado[run] = {
                "listo": verificar_estudiante_listo(run)
            }
        
        return {"success": True, "data": resultado}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class EstudianteCreate(BaseModel):
    run: str
    nombres: str
    apellidos: str
    carrera: str
    modalidad: str
    email: Optional[str] = None


class EstudianteUpdate(BaseModel):
    nombres: Optional[str] = None
    apellidos: Optional[str] = None
    carrera: Optional[str] = None
    modalidad: Optional[str] = None
    email: Optional[str] = None


@router.get("/")
async def listar_estudiantes_endpoint(
    q: Optional[str] = Query(None, description="Búsqueda por RUN o nombre"),
    carrera: Optional[str] = Query(None, description="Filtrar por carrera"),
    modalidad: Optional[str] = Query(None, description="Filtrar por modalidad"),
    listo: Optional[bool] = Query(None, description="Filtrar por estudiantes listos")
):
    """Lista estudiantes con filtros opcionales."""
    try:
        estudiantes = buscar_estudiantes(termino=q, carrera=carrera)
        
        # Filtrar por modalidad
        if modalidad:
            estudiantes = [e for e in estudiantes if e.get('modalidad') == modalidad]
        
        # Filtrar por estudiantes listos
        if listo is not None:
            runs_list = [e['run'] for e in estudiantes]
            if runs_list:
                # Obtener estado de checklist para todos
                estado_checklist = {}
                for run in runs_list:
                    estado_checklist[run] = verificar_estudiante_listo(run)
                
                # Filtrar según el estado
                estudiantes = [
                    e for e in estudiantes 
                    if estado_checklist.get(e['run'], False) == listo
                ]
        
        return {
            "success": True,
            "data": estudiantes,
            "count": len(estudiantes)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{run}")
async def obtener_estudiante_endpoint(run: str):
    """Obtiene un estudiante por su RUN."""
    try:
        estudiante = obtener_estudiante(run)
        if not estudiante:
            raise HTTPException(status_code=404, detail="Estudiante no encontrado")
        
        # Convertir a dict
        if hasattr(estudiante, '__dict__'):
            estudiante_dict = {
                'run': estudiante.run,
                'nombres': estudiante.nombres,
                'apellidos': estudiante.apellidos,
                'nombre_completo': estudiante.nombre_completo,
                'carrera': estudiante.carrera,
                'modalidad': estudiante.modalidad,
                'email': getattr(estudiante, 'email', None)
            }
        else:
            estudiante_dict = estudiante
        
        return {"success": True, "data": estudiante_dict}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/")
async def crear_estudiante_endpoint(estudiante: EstudianteCreate):
    """Crea un nuevo estudiante."""
    try:
        resultado = crear_estudiante(
            run=estudiante.run,
            nombres=estudiante.nombres,
            apellidos=estudiante.apellidos,
            carrera=estudiante.carrera,
            modalidad=estudiante.modalidad,
            email=estudiante.email
        )
        
        if resultado[0]:
            return {"success": True, "message": "Estudiante creado correctamente"}
        else:
            raise HTTPException(status_code=400, detail=resultado[1])
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{run}")
async def actualizar_estudiante_endpoint(run: str, estudiante: EstudianteUpdate):
    """Actualiza un estudiante existente."""
    try:
        datos = estudiante.dict(exclude_unset=True)
        resultado = actualizar_estudiante(run, **datos)
        
        if resultado[0]:
            return {"success": True, "message": "Estudiante actualizado correctamente"}
        else:
            raise HTTPException(status_code=400, detail=resultado[1])
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{run}")
async def eliminar_estudiante_endpoint(run: str):
    """Elimina un estudiante."""
    try:
        resultado = eliminar_estudiante(run)
        
        if resultado[0]:
            return {"success": True, "message": "Estudiante eliminado correctamente"}
        else:
            raise HTTPException(status_code=400, detail=resultado[1])
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/carreras/lista")
async def listar_carreras_endpoint():
    """Obtiene la lista de carreras disponibles."""
    try:
        carreras = obtener_carreras()
        return {"success": True, "data": carreras}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
