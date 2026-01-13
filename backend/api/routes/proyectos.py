"""API Routes para gestión de proyectos."""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List, Dict
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from database import get_session_context, Proyecto, Estudiante, Comision, Expediente

router = APIRouter(prefix="/api/proyectos", tags=["proyectos"])


@router.get("/test")
async def test_proyectos():
    """Endpoint de prueba para verificar que hay proyectos en la BD."""
    try:
        from sqlalchemy import func
        with get_session_context() as session:
            total = session.query(func.count(Proyecto.id)).scalar() or 0
            # Obtener algunos proyectos de ejemplo
            proyectos_ejemplo = session.query(Proyecto).limit(5).all()
            return {
                "success": True,
                "total_proyectos": total,
                "ejemplos": [
                    {
                        "id": p.id,
                        "estudiante_run1": p.estudiante_run1,
                        "semestre": p.semestre,
                        "titulo": p.titulo
                    }
                    for p in proyectos_ejemplo
                ]
            }
    except Exception as e:
        import traceback
        return {
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }


def buscar_proyectos(termino: Optional[str] = None, carrera: Optional[str] = None, semestre: Optional[str] = None, limite: int = 100, offset: int = 0) -> List[Dict]:
    """Busca proyectos y retorna lista de diccionarios (igual que buscar_estudiantes)."""
    try:
        from loguru import logger
        from sqlalchemy import or_, func
        
        with get_session_context() as session:
            # Consulta base: obtener proyectos
            query = session.query(Proyecto)
            
            # Si hay filtro de término, buscar en título o RUN
            if termino:
                termino_like = f"%{termino}%"
                query = query.filter(
                    or_(
                        Proyecto.estudiante_run1.ilike(termino_like),
                        Proyecto.titulo.ilike(termino_like)
                    )
                )
            
            # Si hay filtro de carrera, necesitamos hacer join con Estudiante
            if carrera and carrera != "Todas":
                query = query.join(Estudiante, Proyecto.estudiante_run1 == Estudiante.run)
                query = query.filter(Estudiante.carrera == carrera)
            
            # Si hay filtro de semestre, aplicar directamente en SQL
            if semestre:
                query = query.filter(Proyecto.semestre == semestre)
            
            # Aplicar paginación directamente en SQL (igual que buscar_estudiantes)
            proyectos = query.order_by(Proyecto.created_at.desc()).offset(offset).limit(limite).all()
            
            proyectos_data = []
            for proyecto in proyectos:
                try:
                    # Obtener comisión
                    comision = session.query(Comision).filter(Comision.proyecto_id == proyecto.id).first()
                    
                    # Obtener título - mostrar None si no existe
                    titulo = proyecto.titulo if proyecto.titulo and proyecto.titulo.strip() else None
                    
                    proyecto_dict = {
                        'id': proyecto.id,
                        'titulo': titulo,
                        'run_estudiante1': proyecto.estudiante_run1,
                        'run_estudiante2': proyecto.estudiante_run2,
                        'semestre': proyecto.semestre,
                        'modalidad_titulacion': proyecto.modalidad_titulacion,
                        'profesor_guia': comision.profesor_guia if comision else None
                    }
                    proyectos_data.append(proyecto_dict)
                except Exception as e:
                    import traceback
                    logger.error(f"Error procesando proyecto {proyecto.id}: {e}")
                    logger.debug(traceback.format_exc())
                    continue
            
            return proyectos_data
    except Exception as e:
        import traceback
        from loguru import logger
        logger.error(f"Error en buscar_proyectos: {e}")
        logger.debug(traceback.format_exc())
        return []


@router.get("/semestres/lista")
async def obtener_semestres():
    """Obtiene lista de semestres únicos."""
    try:
        with get_session_context() as session:
            semestres = session.query(Proyecto.semestre).distinct().order_by(Proyecto.semestre.desc()).all()
            return {
                "success": True,
                "data": [s[0] for s in semestres]
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def contar_proyectos_filtrados(termino: Optional[str] = None, carrera: Optional[str] = None, semestre: Optional[str] = None) -> int:
    """Cuenta proyectos filtrados."""
    try:
        from sqlalchemy import or_, func
        with get_session_context() as session:
            query = session.query(func.count(Proyecto.id))
            
            if termino:
                termino_like = f"%{termino}%"
                query = query.filter(
                    or_(
                        Proyecto.estudiante_run1.ilike(termino_like),
                        Proyecto.titulo.ilike(termino_like)
                    )
                )
            
            if carrera and carrera != "Todas":
                query = query.join(Estudiante, Proyecto.estudiante_run1 == Estudiante.run)
                query = query.filter(Estudiante.carrera == carrera)
            
            if semestre:
                query = query.filter(Proyecto.semestre == semestre)
            
            return query.scalar() or 0
    except Exception as e:
        return 0


@router.get("/")
async def listar_proyectos_endpoint(
    q: Optional[str] = Query(None, description="Búsqueda por RUN, nombre o título"),
    carrera: Optional[str] = Query(None, description="Filtrar por carrera"),
    semestre: Optional[str] = Query(None, description="Filtrar por semestre"),
    pagina: int = Query(1, ge=1, description="Número de página"),
    filas_por_pagina: int = Query(10, ge=1, le=100, description="Filas por página")
):
    """Lista proyectos con filtros opcionales y paginación."""
    try:
        
        # Calcular offset (igual que en operaciones masivas)
        offset = (pagina - 1) * filas_por_pagina
        
        # Obtener proyectos paginados (igual que en operaciones masivas)
        proyectos_paginados = buscar_proyectos(
            termino=q,
            carrera=carrera,
            semestre=semestre,
            limite=filas_por_pagina,
            offset=offset
        )
        
        # Contar total (igual que en operaciones masivas)
        total = contar_proyectos_filtrados(termino=q, carrera=carrera, semestre=semestre)
        total_paginas = (total + filas_por_pagina - 1) // filas_por_pagina if total > 0 else 1
        
        return {
            "success": True,
            "data": {
                "proyectos": proyectos_paginados,
                "paginacion": {
                    "pagina_actual": pagina,
                    "filas_por_pagina": filas_por_pagina,
                    "total_registros": total,
                    "total_paginas": total_paginas,
                    "tiene_anterior": pagina > 1,
                    "tiene_siguiente": pagina < total_paginas
                }
            },
            "count": len(proyectos_paginados)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{proyecto_id}")
async def obtener_proyecto_endpoint(proyecto_id: int):
    """Obtiene un proyecto por su ID."""
    try:
        proyectos = buscar_proyectos()
        proyecto = next((p for p in proyectos if p.get('id') == proyecto_id), None)
        
        if not proyecto:
            raise HTTPException(status_code=404, detail="Proyecto no encontrado")
        
        return {"success": True, "data": proyecto}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
