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


def buscar_proyectos(termino: Optional[str] = None, carrera: Optional[str] = None) -> List[Dict]:
    """Busca proyectos y retorna lista de diccionarios (igual que buscar_estudiantes)."""
    try:
        with get_session_context() as session:
            # Siempre hacer join con Estudiante para tener acceso a carrera
            query = session.query(Proyecto).join(Estudiante, Proyecto.estudiante_run1 == Estudiante.run)
            
            if termino:
                termino_like = f"%{termino}%"
                from sqlalchemy import or_
                query = query.filter(
                    or_(
                        Estudiante.run.ilike(termino_like),
                        Estudiante.nombres.ilike(termino_like),
                        Estudiante.apellidos.ilike(termino_like),
                        Proyecto.titulo.ilike(termino_like)
                    )
                )
            
            if carrera and carrera != "Todas":
                query = query.filter(Estudiante.carrera == carrera)
            
            proyectos = query.order_by(Proyecto.created_at.desc()).limit(500).all()
            
            proyectos_data = []
            for proyecto in proyectos:
                try:
                    estudiante_1 = session.query(Estudiante).filter(Estudiante.run == proyecto.estudiante_run1).first()
                    estudiante_2 = None
                    if proyecto.estudiante_run2:
                        estudiante_2 = session.query(Estudiante).filter(Estudiante.run == proyecto.estudiante_run2).first()
                    
                    comision = session.query(Comision).filter(Comision.proyecto_id == proyecto.id).first()
                    expediente = session.query(Expediente).filter(Expediente.proyecto_id == proyecto.id).first()
                    
                    # Obtener estado del expediente de forma segura
                    estado_expediente = None
                    if expediente and hasattr(expediente, 'estado'):
                        try:
                            estado_expediente = expediente.estado.value if hasattr(expediente.estado, 'value') else str(expediente.estado)
                        except:
                            pass
                    
                    proyecto_dict = {
                        'id': proyecto.id,
                        'estudiante_run1': proyecto.estudiante_run1,
                        'estudiante_nombre1': f"{estudiante_1.nombres} {estudiante_1.apellidos}" if estudiante_1 else "N/A",
                        'estudiante_carrera1': estudiante_1.carrera if estudiante_1 else None,
                        'estudiante_run2': proyecto.estudiante_run2,
                        'estudiante_nombre2': f"{estudiante_2.nombres} {estudiante_2.apellidos}" if estudiante_2 else None,
                        'estudiante_carrera2': estudiante_2.carrera if estudiante_2 else None,
                        'semestre': proyecto.semestre,
                        'modalidad_titulacion': proyecto.modalidad_titulacion,
                        'titulo': proyecto.titulo or "Sin título",
                        'link_documento': proyecto.link_documento,
                        'fecha_inicio': proyecto.created_at.strftime("%d/%m/%Y") if proyecto.created_at else None,
                        'fecha_actualizacion': proyecto.updated_at.strftime("%d/%m/%Y") if proyecto.updated_at else None,
                        'profesor_guia': comision.profesor_guia if comision else None,
                        'corrector_1': comision.corrector_1 if comision else None,
                        'corrector_2': comision.corrector_2 if comision else None,
                        'estado_expediente': estado_expediente,
                        'observaciones': expediente.observaciones if expediente else None,
                        'titulado': expediente.titulado if expediente else False,
                        'semestre_titulacion': expediente.semestre_titulacion if expediente else None
                    }
                    proyectos_data.append(proyecto_dict)
                except Exception as e:
                    import traceback
                    print(f"Error procesando proyecto {proyecto.id}: {e}")
                    continue
            
            return proyectos_data
    except Exception as e:
        import traceback
        print(f"Error en buscar_proyectos: {e}")
        print(traceback.format_exc())
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


@router.get("/")
async def listar_proyectos_endpoint(
    q: Optional[str] = Query(None, description="Búsqueda por RUN, nombre o título"),
    carrera: Optional[str] = Query(None, description="Filtrar por carrera"),
    semestre: Optional[str] = Query(None, description="Filtrar por semestre")
):
    """Lista proyectos con filtros opcionales."""
    try:
        proyectos = buscar_proyectos(termino=q, carrera=carrera)
        
        # Filtrar por semestre
        if semestre:
            proyectos = [p for p in proyectos if p.get('semestre') == semestre]
        
        return {
            "success": True,
            "data": proyectos,
            "count": len(proyectos)
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
