# pages/3_Documentos.py
"""
Validación de Documentos Habilitantes (RF-02).
Checklist visual por estudiante con upload de PDFs.
"""

import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import datetime

st.set_page_config(page_title="Documentos | SGTE", page_icon="📊", layout="wide")

from database import get_session_context, Documento, Estudiante, TipoDocumento
from services.estudiantes import buscar_estudiantes, formatear_run
from config import get_config
from services.ui import inject_custom_css, render_global_sidebar

# Inyectar estilos
inject_custom_css()
    
# Renderizar Sidebar Global
render_global_sidebar(current_page="Documentos")


# ============================================
# CONFIGURACIÓN DE DOCUMENTOS
# ============================================

DOCUMENTOS_REQUERIDOS = {
    "titulo": [
        TipoDocumento.BIENESTAR,
        TipoDocumento.FINANZAS_TITULO,
        TipoDocumento.BIBLIOTECA,
        TipoDocumento.SDT
    ],
    "licenciatura": [
        TipoDocumento.BIENESTAR,
        TipoDocumento.FINANZAS_LICENCIA,
        TipoDocumento.BIBLIOTECA
    ]
}

NOMBRES_DOCUMENTOS = {
    TipoDocumento.BIENESTAR: "📋 Bienestar Estudiantil",
    TipoDocumento.FINANZAS_TITULO: "💰 Finanzas (Título)",
    TipoDocumento.FINANZAS_LICENCIA: "💰 Finanzas (Licenciatura)",
    TipoDocumento.BIBLIOTECA: "📚 Biblioteca",
    TipoDocumento.SDT: "📝 SDT (Secretaría Docente)",
    TipoDocumento.MEMORANDUM: "📎 Memorándum",
    TipoDocumento.ACTA: "📜 Acta",
    TipoDocumento.OTRO: "📁 Otro"
}


# ============================================
# FUNCIONES
# ============================================

def obtener_documentos_estudiante(run: str) -> dict:
    """Obtiene documentos de un estudiante como diccionario."""
    try:
        with get_session_context() as session:
            docs = session.query(Documento).filter(
                Documento.estudiante_run == run
            ).all()
            
            return {
                doc.tipo: {
                    "id": doc.id,
                    "path": doc.path,
                    "validado": doc.validado,
                    "uploaded_at": doc.uploaded_at
                }
                for doc in docs
            }
    except Exception as e:
        st.error(f"Error: {e}")
        return {}


def guardar_documento(run: str, tipo: TipoDocumento, archivo) -> tuple[bool, str]:
    """Guarda un documento PDF para un estudiante."""
    config = get_config()
    
    try:
        # Crear carpeta del estudiante
        run_limpio = run.replace(".", "").replace("-", "")
        carpeta = Path(config.paths.expedientes_root) / run_limpio
        carpeta.mkdir(parents=True, exist_ok=True)
        
        # Guardar archivo
        nombre_archivo = f"{tipo.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        ruta = carpeta / nombre_archivo
        
        with open(ruta, "wb") as f:
            f.write(archivo.getbuffer())
        
        # Registrar en BD
        with get_session_context() as session:
            # Verificar si ya existe
            doc_existente = session.query(Documento).filter(
                Documento.estudiante_run == run,
                Documento.tipo == tipo
            ).first()
            
            if doc_existente:
                doc_existente.path = str(ruta)
                doc_existente.uploaded_at = datetime.now()
                doc_existente.validado = False
            else:
                nuevo_doc = Documento(
                    estudiante_run=run,
                    tipo=tipo,
                    path=str(ruta),
                    validado=False
                )
                session.add(nuevo_doc)
        
        return True, f"Documento guardado: {ruta.name}"
        
    except Exception as e:
        return False, f"Error: {e}"


def validar_documento(doc_id: int, validado: bool) -> bool:
    """Marca un documento como validado/no validado."""
    try:
        with get_session_context() as session:
            doc = session.query(Documento).filter(Documento.id == doc_id).first()
            if doc:
                doc.validado = validado
                doc.validated_at = datetime.now() if validado else None
                return True
        return False
    except:
        return False


# ============================================
# ESTILOS
# ============================================

# Estilos inyectados globalmente via ui.inject_custom_css


# ============================================
# INTERFAZ
# ============================================

st.title("Documentos Habilitantes")

# Selector de estudiante
col1, col2 = st.columns([3, 1])

with col1:
    termino = st.text_input("🔍 Buscar estudiante", placeholder="RUN o nombre...")

with col2:
    st.write("")
    st.write("")
    if st.button("Refrescar"):
        st.rerun()

# Buscar estudiantes
if termino:
    estudiantes = buscar_estudiantes(termino=termino, limite=20)
else:
    estudiantes = buscar_estudiantes(limite=50)

if estudiantes:
    # Selector
    opciones = {e['run']: f"{e['run']} - {e['nombre_completo']}" for e in estudiantes}
    run_seleccionado = st.selectbox(
        "Seleccione estudiante",
        options=list(opciones.keys()),
        format_func=lambda x: opciones[x]
    )
    
    if run_seleccionado:
        st.markdown("---")
        
        # Info del estudiante
        est = next((e for e in estudiantes if e['run'] == run_seleccionado), None)
        if est:
            col1, col2, col3 = st.columns(3)
            col1.metric("Estudiante", est['nombre_completo'])
            col2.metric("Carrera", est['carrera'][:30] + "..." if len(est['carrera']) > 30 else est['carrera'])
            col3.metric("RUN", est['run'])
        
        st.markdown("---")
        
        # Checklist de documentos
        st.subheader("Checklist de Documentos")
        
        documentos = obtener_documentos_estudiante(run_seleccionado)
        
        # Mostrar checklist
        col_check, col_upload = st.columns([2, 1])
        
        with col_check:
            for tipo in TipoDocumento:
                if tipo in [TipoDocumento.MEMORANDUM, TipoDocumento.ACTA, TipoDocumento.OTRO]:
                    continue
                
                nombre = NOMBRES_DOCUMENTOS.get(tipo, tipo.value)
                doc = documentos.get(tipo)
                
                if doc and doc['validado']:
                    icono = "✅"
                    clase = "doc-valid"
                    estado = "Validado"
                elif doc:
                    icono = "📎"
                    clase = "doc-pending"
                    estado = "Pendiente validación"
                else:
                    icono = "⭕"
                    clase = "doc-invalid"
                    estado = "Faltante"
                
                st.markdown(f"""
                <div class="doc-card {clase}">
                    <strong>{icono} {nombre}</strong><br>
                    <small>{estado}</small>
                </div>
                """, unsafe_allow_html=True)
                
                # Botón de validación si existe documento
                if doc and not doc['validado']:
                    if st.button(f"✓ Validar {tipo.value}", key=f"val_{tipo.value}"):
                        if validar_documento(doc['id'], True):
                            st.success("Documento validado")
                            st.rerun()
        
        with col_upload:
            st.markdown("### 📤 Subir Documento")
            
            tipo_subir = st.selectbox(
                "Tipo de documento",
                options=[t for t in TipoDocumento if t not in [TipoDocumento.MEMORANDUM, TipoDocumento.ACTA]],
                format_func=lambda x: NOMBRES_DOCUMENTOS.get(x, x.value)
            )
            
            archivo = st.file_uploader(
                "Seleccione PDF",
                type=['pdf'],
                key="upload_doc"
            )
            
            if archivo:
                if st.button("Guardar Documento", type="primary", use_container_width=True):
                    exito, msg = guardar_documento(run_seleccionado, tipo_subir, archivo)
                    if exito:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)
        
        # Resumen
        st.markdown("---")
        total = len([t for t in TipoDocumento if t not in [TipoDocumento.MEMORANDUM, TipoDocumento.ACTA, TipoDocumento.OTRO]])
        validados = len([d for d in documentos.values() if d['validado']])
        
        progreso = validados / total if total > 0 else 0
        st.progress(progreso, f"Progreso: {validados}/{total} documentos validados")
        
        if progreso == 1.0:
            st.success("🎉 ¡Documentación completa! El estudiante está listo para envío.")

else:
    st.info("No hay estudiantes registrados. Registre estudiantes primero.")
