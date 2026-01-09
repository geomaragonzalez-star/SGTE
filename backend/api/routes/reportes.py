"""API Routes para reportes y exportación."""
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from typing import Optional
import pandas as pd
from io import BytesIO
from datetime import datetime
import sys
from pathlib import Path
from sqlalchemy import func

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from database import get_session_context, Estudiante, Proyecto, Expediente, Documento, Bitacora
from services.excel_export import exportar_estudiantes, generar_reporte_maestro, obtener_datos_completos
from config import get_config
from sqlalchemy import func

router = APIRouter(prefix="/api/reportes", tags=["reportes"])


@router.get("/estudiantes")
async def generar_reporte_estudiantes():
    """Genera reporte de estudiantes en Excel."""
    try:
        excel_bytes, filename, count = exportar_estudiantes()
        
        if not excel_bytes or count == 0:
            raise HTTPException(status_code=404, detail="No hay estudiantes para exportar")
        
        return StreamingResponse(
            BytesIO(excel_bytes),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/maestro")
async def generar_reporte_maestro_endpoint():
    """Genera reporte maestro completo."""
    try:
        excel_bytes, filename, count = generar_reporte_maestro()
        
        if not excel_bytes or count == 0:
            raise HTTPException(status_code=404, detail="No hay datos para exportar")
        
        return StreamingResponse(
            BytesIO(excel_bytes),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/bitacora")
async def generar_reporte_bitacora(limit: int = 1000):
    """Genera reporte de bitácora."""
    try:
        with get_session_context() as session:
            registros = session.query(Bitacora).order_by(
                Bitacora.timestamp.desc()
            ).limit(limit).all()
            
            data = [{
                "FECHA": r.timestamp.strftime("%d/%m/%Y %H:%M:%S"),
                "TABLA": r.tabla,
                "REGISTRO": r.registro_id,
                "ACCION": r.accion,
                "USUARIO": r.usuario or "",
                "DESCRIPCION": r.descripcion or ""
            } for r in registros]
            
            df = pd.DataFrame(data)
            
            if df.empty:
                raise HTTPException(status_code=404, detail="No hay registros en la bitácora")
            
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Bitacora')
            
            output.seek(0)
            filename = f"Bitacora_{datetime.now().strftime('%Y%m%d')}.xlsx"
            
            return StreamingResponse(
                BytesIO(output.read()),
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/estadisticas")
async def obtener_estadisticas():
    """Obtiene estadísticas generales del sistema."""
    try:
        with get_session_context() as session:
            stats = {
                "total_estudiantes": session.query(func.count(Estudiante.run)).scalar() or 0,
                "total_proyectos": session.query(func.count(Proyecto.id)).scalar() or 0,
                "documentos_cargados": session.query(func.count(Documento.id)).scalar() or 0,
                "acciones_bitacora": session.query(func.count(Bitacora.id)).scalar() or 0
            }
            
            return {"success": True, "data": stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/backup")
async def descargar_backup():
    """Descarga un respaldo de la base de datos."""
    try:
        config = get_config()
        db_path = Path(config.paths.db_path)
        
        if not db_path.exists():
            raise HTTPException(status_code=404, detail="Base de datos no encontrada")
        
        with open(db_path, 'rb') as f:
            db_bytes = f.read()
        
        filename = f"sgte_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        
        return StreamingResponse(
            BytesIO(db_bytes),
            media_type="application/octet-stream",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
