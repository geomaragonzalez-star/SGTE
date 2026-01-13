"""
FastAPI Backend para SGTE
Reutiliza toda la lógica de servicios existente
"""

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
from datetime import datetime
import sys

# Agregar el directorio raíz al path para imports
ROOT_DIR = Path(__file__).parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Importar config
from config import get_config

# Importar routers - usar path absoluto desde raíz
# Cuando uvicorn ejecuta backend.api.main, el path raíz ya está en sys.path
from backend.api.routes import estudiantes, documentos, expedientes, reportes, dashboard, operaciones, proyectos

# Crear app FastAPI
app = FastAPI(
    title="SGTE API",
    description="Sistema de Gestión de Titulaciones y Expedientes",
    version="2.0.0"
)

# Configurar templates Jinja2
BASE_DIR = Path(__file__).parent.parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "frontend" / "templates"))

# Montar archivos estáticos
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "frontend" / "static")), name="static")
app.mount("/assets", StaticFiles(directory=str(BASE_DIR / "assets")), name="assets")

# Incluir routers
app.include_router(estudiantes.router)
app.include_router(documentos.router)
app.include_router(expedientes.router)
app.include_router(reportes.router)
app.include_router(dashboard.router)
app.include_router(operaciones.router)
app.include_router(proyectos.router)


# ============================================
# RUTAS DE FRONTEND (Jinja2 Templates)
# ============================================

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Página principal."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    """Dashboard principal."""
    # Obtener métricas desde la API
    from backend.api.routes.dashboard import obtener_metricas, obtener_distribucion_carreras, obtener_ultimos_registros
    from backend.api.routes.reportes import obtener_estadisticas
    from datetime import datetime
    import os
    from pathlib import Path
    
    try:
        metricas_resp = await obtener_metricas()
        metricas = metricas_resp["data"]
        
        distribucion_resp = await obtener_distribucion_carreras()
        distribucion = distribucion_resp["data"]
        
        ultimos_resp = await obtener_ultimos_registros()
        ultimos = ultimos_resp["data"]
    except:
        metricas = {
            "total_estudiantes": 0,
            "total_proyectos": 0,
            "pendientes": 0,
            "en_proceso": 0,
            "listos": 0,
            "enviados": 0,
            "titulados": 0
        }
        distribucion = []
        ultimos = []
    
    # Obtener estadísticas de reportes
    try:
        stats_resp = await obtener_estadisticas()
        stats = stats_resp["data"]
    except:
        stats = {
            "total_estudiantes": 0,
            "total_proyectos": 0,
            "documentos_cargados": 0,
            "acciones_bitacora": 0
        }
    
    # Información de base de datos
    config = get_config()
    db_path = Path(config.paths.db_path)
    db_modified = None
    db_size = 0
    
    if db_path.exists():
        stat = os.stat(db_path)
        db_modified = datetime.fromtimestamp(stat.st_mtime).strftime("%d/%m/%Y %H:%M:%S")
        db_size = stat.st_size / 1024  # KB
    
    fecha_actualizacion = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "metricas": metricas,
            "distribucion": distribucion,
            "ultimos": ultimos,
            "fecha_actualizacion": fecha_actualizacion,
            "stats": stats,
            "db_modified": db_modified,
            "db_size": db_size
        }
    )


@app.get("/estudiantes", response_class=HTMLResponse)
async def estudiantes_page(request: Request, q: str = None, carrera: str = None, modalidad: str = None, listo: str = None):
    """Página de gestión de estudiantes."""
    # Obtener carreras para el select (solo esto se necesita del servidor)
    from services.estudiantes import obtener_carreras
    
    carreras = obtener_carreras()
    
    # Convertir listo a bool
    listo_bool = None
    if listo == "true":
        listo_bool = True
    elif listo == "false":
        listo_bool = False
    
    # NO pasar estudiantes al template - se cargarán vía JavaScript
    return templates.TemplateResponse(
        "estudiantes/lista.html",
        {
            "request": request,
            "estudiantes": [],  # Vacío - se carga vía JavaScript
            "query": q or "",
            "carrera_filter": carrera or "",
            "modalidad_filter": modalidad or "",
            "listo_filter": listo_bool,
            "carreras": carreras
        }
    )


@app.get("/proyectos", response_class=HTMLResponse)
async def proyectos_page(request: Request, q: str = None, carrera: str = None, semestre: str = None):
    """Página de gestión de proyectos."""
    try:
        # Obtener solo carreras para el select (los proyectos se cargarán vía JavaScript)
        from services.estudiantes import obtener_carreras
        from database import get_session_context, Proyecto
        
        carreras = []
        semestres = []
        
        # Obtener carreras para el select
        try:
            carreras = obtener_carreras()
        except Exception as e:
            print(f"ERROR obteniendo carreras: {e}")
            carreras = []
        
        # Obtener semestres desde la base de datos directamente
        try:
            with get_session_context() as session:
                semestres_query = session.query(Proyecto.semestre).distinct().order_by(Proyecto.semestre.desc()).all()
                semestres = [s[0] for s in semestres_query if s[0]]
        except Exception as e:
            import traceback
            print(f"ERROR obteniendo semestres: {e}")
            print(traceback.format_exc())
            semestres = []
        
        # NO pasar proyectos al template - se cargarán vía JavaScript con paginación
        return templates.TemplateResponse(
            "proyectos/lista.html",
            {
                "request": request,
                "proyectos": [],  # Vacío - se carga vía JavaScript
                "query": q or "",
                "carrera_filter": carrera or "",
                "semestre_filter": semestre or "",
                "carreras": carreras,
                "semestres": semestres
            }
        )
    except Exception as e:
        import traceback
        error_msg = f"ERROR CRÍTICO en proyectos_page: {str(e)}\n{traceback.format_exc()}"
        print(error_msg)
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "message": f"Error al cargar proyectos: {str(e)}"
            },
            status_code=500
        )


@app.get("/estudiantes/nuevo", response_class=HTMLResponse)
async def estudiante_nuevo(request: Request):
    """Formulario para crear nuevo estudiante."""
    return templates.TemplateResponse("estudiantes/crear.html", {"request": request})


@app.get("/estudiantes/{run}", response_class=HTMLResponse)
async def estudiante_detalle(request: Request, run: str):
    """Detalle de un estudiante."""
    from services.estudiantes import obtener_estudiante
    
    estudiante = obtener_estudiante(run)
    if not estudiante:
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "message": "Estudiante no encontrado"},
            status_code=404
        )
    
    # Convertir a dict si es objeto SQLAlchemy
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
    
    return templates.TemplateResponse(
        "estudiantes/detalle.html",
        {"request": request, "estudiante": estudiante_dict}
    )


@app.get("/estudiantes/{run}/editar", response_class=HTMLResponse)
async def estudiante_editar(request: Request, run: str):
    """Formulario para editar un estudiante."""
    from services.estudiantes import obtener_estudiante
    
    estudiante = obtener_estudiante(run)
    if not estudiante:
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "message": "Estudiante no encontrado"},
            status_code=404
        )
    
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
    
    return templates.TemplateResponse(
        "estudiantes/editar.html",
        {"request": request, "estudiante": estudiante_dict}
    )


@app.get("/documentos/{run}", response_class=HTMLResponse)
async def documentos_estudiante(request: Request, run: str):
    """Página de documentos de un estudiante específico."""
    from services.estudiantes import obtener_estudiante
    
    estudiante = obtener_estudiante(run)
    if not estudiante:
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "message": "Estudiante no encontrado"},
            status_code=404
        )
    
    # Convertir a dict
    if hasattr(estudiante, '__dict__'):
        estudiante_dict = {
            'run': estudiante.run,
            'nombre_completo': estudiante.nombre_completo,
            'carrera': estudiante.carrera,
        }
    else:
        estudiante_dict = estudiante
    
    return templates.TemplateResponse(
        "documentos/detalle.html",
        {"request": request, "estudiante": estudiante_dict}
    )


@app.get("/informaciones", response_class=HTMLResponse)
async def informaciones_page(request: Request):
    """Página de informaciones sobre documentos requeridos."""
    return templates.TemplateResponse(
        "documentos/lista.html",
        {
            "request": request
        }
    )


@app.get("/documentos", response_class=HTMLResponse)
async def documentos_page(request: Request, q: str = None):
    """Página de gestión de documentos."""
    from services.estudiantes import buscar_estudiantes
    
    # Buscar estudiantes
    if q:
        estudiantes_data = buscar_estudiantes(termino=q, limite=50)
    else:
        estudiantes_data = buscar_estudiantes(limite=50)
    
    return templates.TemplateResponse(
        "documentos/lista.html",
        {
            "request": request,
            "estudiantes": estudiantes_data,
            "query": q
        }
    )


@app.get("/operaciones-masivas", response_class=HTMLResponse)
async def operaciones_masivas_page(request: Request):
    """Página de operaciones masivas."""
    from services.estudiantes import buscar_estudiantes
    
    estudiantes_data = buscar_estudiantes(limite=200)
    
    return templates.TemplateResponse(
        "operaciones/lista.html",
        {
            "request": request,
            "estudiantes": estudiantes_data
        }
    )




# ============================================
# HEALTH CHECK
# ============================================

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "version": "2.0.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
