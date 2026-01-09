"""API Routes para gestión de documentos."""
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from typing import Optional, List, Dict
from datetime import datetime
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from database import get_session_context, Documento, Estudiante, TipoDocumento
from services.estudiantes import buscar_estudiantes
from config import get_config

router = APIRouter(prefix="/api/documentos", tags=["documentos"])


# Documentos requeridos para solicitar apertura de expediente
DOCUMENTOS_REQUERIDOS = [
    TipoDocumento.BIENESTAR,
    TipoDocumento.FINANZAS_TITULO,
    TipoDocumento.FINANZAS_LICENCIA,
    TipoDocumento.BIBLIOTECA,
    TipoDocumento.SDT,
    TipoDocumento.MEMORANDUM
]

NOMBRES_DOCUMENTOS = {
    TipoDocumento.BIENESTAR: "Bienestar Estudiantil",
    TipoDocumento.FINANZAS_TITULO: "Finanzas (Título)",
    TipoDocumento.FINANZAS_LICENCIA: "Finanzas (Licenciatura)",
    TipoDocumento.BIBLIOTECA: "Biblioteca",
    TipoDocumento.SDT: "SDT (Secretaría Docente)",
    TipoDocumento.MEMORANDUM: "Memorándum de Solicitud",
    TipoDocumento.ACTA: "Acta",
    TipoDocumento.OTRO: "Otro"
}


@router.get("/")
async def listar_documentos(estudiante_run: Optional[str] = None):
    """Lista documentos, opcionalmente filtrados por estudiante."""
    try:
        with get_session_context() as session:
            query = session.query(Documento)
            if estudiante_run:
                query = query.filter(Documento.estudiante_run == estudiante_run)
            
            documentos = query.all()
            
            return {
                "success": True,
                "data": [{
                    "id": d.id,
                    "estudiante_run": d.estudiante_run,
                    "tipo": d.tipo.value,
                    "path": d.path,
                    "validado": d.validado,
                    "uploaded_at": d.uploaded_at.isoformat() if d.uploaded_at else None,
                    "validated_at": d.validated_at.isoformat() if d.validated_at else None
                } for d in documentos],
                "count": len(documentos)
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/estudiante/{run}")
async def obtener_documentos_estudiante(run: str):
    """Obtiene todos los documentos de un estudiante."""
    try:
        with get_session_context() as session:
            docs = session.query(Documento).filter(
                Documento.estudiante_run == run
            ).all()
            
            documentos_dict = {
                doc.tipo.value: {
                    "id": doc.id,
                    "path": doc.path,
                    "validado": doc.validado,
                    "uploaded_at": doc.uploaded_at.isoformat() if doc.uploaded_at else None,
                    "validated_at": doc.validated_at.isoformat() if doc.validated_at else None
                }
                for doc in docs
            }
            
            return {"success": True, "data": documentos_dict}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/checklist/{run}")
async def obtener_checklist_estudiante(run: str):
    """Obtiene el checklist completo de documentos para un estudiante."""
    try:
        with get_session_context() as session:
            # Verificar que el estudiante existe
            estudiante = session.query(Estudiante).filter(Estudiante.run == run).first()
            if not estudiante:
                raise HTTPException(status_code=404, detail="Estudiante no encontrado")
            
            # Obtener documentos existentes
            docs = session.query(Documento).filter(
                Documento.estudiante_run == run
            ).all()
            
            documentos_dict = {doc.tipo: doc for doc in docs}
            
            # Construir checklist
            checklist = []
            documentos_validados = 0
            documentos_requeridos_validados = 0
            
            # Documentos requeridos
            for tipo_doc in DOCUMENTOS_REQUERIDOS:
                doc = documentos_dict.get(tipo_doc)
                tiene_documento = doc is not None and doc.path is not None
                validado = doc is not None and doc.validado
                
                # Para finanzas, solo uno es requerido (título o licenciatura)
                if tipo_doc == TipoDocumento.FINANZAS_TITULO:
                    # Verificar si tiene título o licenciatura
                    tiene_finanzas = (
                        documentos_dict.get(TipoDocumento.FINANZAS_TITULO) is not None or
                        documentos_dict.get(TipoDocumento.FINANZAS_LICENCIA) is not None
                    )
                    validado_finanzas = (
                        (documentos_dict.get(TipoDocumento.FINANZAS_TITULO) and documentos_dict.get(TipoDocumento.FINANZAS_TITULO).validado) or
                        (documentos_dict.get(TipoDocumento.FINANZAS_LICENCIA) and documentos_dict.get(TipoDocumento.FINANZAS_LICENCIA).validado)
                    )
                    doc_finanzas = documentos_dict.get(TipoDocumento.FINANZAS_TITULO) or documentos_dict.get(TipoDocumento.FINANZAS_LICENCIA)
                    checklist.append({
                        "tipo": tipo_doc.value,
                        "nombre": NOMBRES_DOCUMENTOS[tipo_doc],
                        "requerido": True,
                        "tiene_documento": tiene_finanzas,
                        "validado": validado_finanzas,
                        "id": doc_finanzas.id if doc_finanzas else None,
                        "path": doc_finanzas.path if doc_finanzas else None
                    })
                    if validado_finanzas:
                        documentos_requeridos_validados += 1
                    continue
                elif tipo_doc == TipoDocumento.FINANZAS_LICENCIA:
                    # Saltar licenciatura si ya se procesó título
                    continue
                
                checklist.append({
                    "tipo": tipo_doc.value,
                    "nombre": NOMBRES_DOCUMENTOS[tipo_doc],
                    "requerido": True,
                    "tiene_documento": tiene_documento,
                    "validado": validado,
                    "id": doc.id if doc else None,
                    "path": doc.path if doc else None
                })
                
                if validado:
                    documentos_requeridos_validados += 1
            
            # Documentos opcionales (otros)
            for doc in docs:
                if doc.tipo not in DOCUMENTOS_REQUERIDOS:
                    checklist.append({
                        "tipo": doc.tipo.value,
                        "nombre": NOMBRES_DOCUMENTOS.get(doc.tipo, doc.tipo.value),
                        "requerido": False,
                        "tiene_documento": doc.path is not None,
                        "validado": doc.validado,
                        "id": doc.id,
                        "path": doc.path
                    })
            
            # Determinar si está listo
            total_requeridos = len(DOCUMENTOS_REQUERIDOS) - 1  # -1 porque finanzas_titulo y finanzas_licencia cuentan como uno
            listo_para_solicitar = documentos_requeridos_validados == total_requeridos
            
            return {
                "success": True,
                "data": {
                    "checklist": checklist,
                    "resumen": {
                        "total_requeridos": total_requeridos,
                        "documentos_validados": documentos_requeridos_validados,
                        "documentos_faltantes": total_requeridos - documentos_requeridos_validados,
                        "listo_para_solicitar": listo_para_solicitar
                    }
                }
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload")
async def subir_documento(
    run: str = Form(...),
    tipo: str = Form(...),
    archivo: UploadFile = File(...)
):
    """Sube un documento PDF para un estudiante."""
    try:
        # Validar tipo
        try:
            tipo_doc = TipoDocumento(tipo)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Tipo de documento inválido: {tipo}")
        
        # Validar que es PDF
        if not archivo.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Solo se aceptan archivos PDF")
        
        config = get_config()
        
        # Crear carpeta del estudiante
        run_limpio = run.replace(".", "").replace("-", "")
        carpeta = Path(config.paths.expedientes_root) / run_limpio
        carpeta.mkdir(parents=True, exist_ok=True)
        
        # Guardar archivo
        nombre_archivo = f"{tipo_doc.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        ruta = carpeta / nombre_archivo
        
        contenido = await archivo.read()
        with open(ruta, "wb") as f:
            f.write(contenido)
        
        # Registrar en BD
        with get_session_context() as session:
            # Verificar si ya existe
            doc_existente = session.query(Documento).filter(
                Documento.estudiante_run == run,
                Documento.tipo == tipo_doc
            ).first()
            
            if doc_existente:
                doc_existente.path = str(ruta)
                doc_existente.uploaded_at = datetime.now()
                doc_existente.validado = False
                doc_id = doc_existente.id
            else:
                nuevo_doc = Documento(
                    estudiante_run=run,
                    tipo=tipo_doc,
                    path=str(ruta),
                    validado=False
                )
                session.add(nuevo_doc)
                session.flush()  # Para obtener el ID
                doc_id = nuevo_doc.id
            
            session.commit()
        
        return {
            "success": True,
            "message": "Documento subido correctamente",
            "path": str(ruta),
            "doc_id": doc_id,
            "tipo": tipo_doc.value
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{doc_id}/preview")
async def previsualizar_documento(doc_id: int):
    """Sirve un documento PDF para previsualización."""
    try:
        with get_session_context() as session:
            doc = session.query(Documento).filter(Documento.id == doc_id).first()
            if not doc:
                raise HTTPException(status_code=404, detail="Documento no encontrado")
            
            if not doc.path:
                raise HTTPException(status_code=404, detail="Documento no tiene archivo asociado")
            
            ruta = Path(doc.path)
            if not ruta.exists():
                raise HTTPException(status_code=404, detail="Archivo no encontrado en el sistema")
            
            return FileResponse(
                path=str(ruta),
                media_type="application/pdf",
                filename=ruta.name,
                headers={"Content-Disposition": f"inline; filename={ruta.name}"}
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{doc_id}/validar")
async def validar_documento(doc_id: int, validado: bool = True):
    """Valida o invalida un documento."""
    try:
        with get_session_context() as session:
            doc = session.query(Documento).filter(Documento.id == doc_id).first()
            if not doc:
                raise HTTPException(status_code=404, detail="Documento no encontrado")
            
            doc.validado = validado
            if validado:
                doc.validated_at = datetime.now()
                doc.validated_by = "Sistema"  # En producción, usar usuario autenticado
            else:
                doc.validated_at = None
                doc.validated_by = None
            
            session.commit()
            
            return {
                "success": True,
                "message": f"Documento {'validado' if validado else 'invalidado'} correctamente"
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
