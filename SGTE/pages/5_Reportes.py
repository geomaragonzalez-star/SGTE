# pages/5_Reportes.py
"""
Módulo de Reportes y Exportación (RF-06).
Generación de reportes Excel y respaldo de datos.
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from pathlib import Path
from io import BytesIO

st.set_page_config(page_title="Reportes | SGTE", page_icon="📊", layout="wide")

from database import get_session_context, Estudiante, Proyecto, Expediente, Documento, Bitacora
from config import get_config
from sqlalchemy import func
from services.ui import inject_custom_css, render_global_sidebar

# Inyectar estilos
inject_custom_css()
    
# Renderizar Sidebar Global
render_global_sidebar(current_page="Reportes")


# ============================================
# FUNCIONES DE EXPORTACIÓN
# ============================================

def exportar_estudiantes_excel():
    """Exporta todos los estudiantes a Excel."""
    try:
        with get_session_context() as session:
            estudiantes = session.query(Estudiante).all()
            
            data = [{
                "RUN": e.run,
                "NOMBRES": e.nombres,
                "APELLIDOS": e.apellidos,
                "CARRERA": e.carrera,
                "EMAIL": e.email,
                "FECHA_REGISTRO": e.created_at.strftime("%d/%m/%Y") if e.created_at else ""
            } for e in estudiantes]
            
            return pd.DataFrame(data)
    except Exception as e:
        st.error(f"Error: {e}")
        return pd.DataFrame()


def exportar_reporte_maestro():
    """Genera el reporte maestro completo (RF-06)."""
    try:
        with get_session_context() as session:
            # Query complejo con joins
            resultados = session.query(
                Estudiante.run,
                Estudiante.nombres,
                Estudiante.apellidos,
                Estudiante.carrera,
                Estudiante.email,
                Proyecto.semestre,
                Proyecto.modalidad,
                Proyecto.titulo,
                Expediente.estado,
                Expediente.observaciones,
                Expediente.titulado
            ).outerjoin(
                Proyecto, Proyecto.estudiante_run == Estudiante.run
            ).outerjoin(
                Expediente, Expediente.proyecto_id == Proyecto.id
            ).all()
            
            data = [{
                "R.U.N": r.run,
                "NOMBRES": r.nombres,
                "APELLIDOS": r.apellidos,
                "CARRERA": r.carrera,
                "EMAIL": r.email,
                "SEMESTRE": r.semestre if r.semestre else "",
                "MODALIDAD": r.modalidad.value if r.modalidad else "",
                "TITULO_PROYECTO": r.titulo if r.titulo else "",
                "ESTADO": r.estado.value if r.estado else "sin_expediente",
                "OBSERVACIONES": r.observaciones if r.observaciones else "",
                "TITULADO": "SI" if r.titulado else "NO"
            } for r in resultados]
            
            return pd.DataFrame(data)
    except Exception as e:
        st.error(f"Error generando reporte: {e}")
        return pd.DataFrame()


def exportar_bitacora():
    """Exporta la bitácora de acciones."""
    try:
        with get_session_context() as session:
            registros = session.query(Bitacora).order_by(
                Bitacora.timestamp.desc()
            ).limit(1000).all()
            
            data = [{
                "FECHA": r.timestamp.strftime("%d/%m/%Y %H:%M:%S"),
                "TABLA": r.tabla,
                "REGISTRO": r.registro_id,
                "ACCION": r.accion,
                "USUARIO": r.usuario or "",
                "DESCRIPCION": r.descripcion or ""
            } for r in registros]
            
            return pd.DataFrame(data)
    except Exception as e:
        st.error(f"Error: {e}")
        return pd.DataFrame()


def df_to_excel(df: pd.DataFrame) -> bytes:
    """Convierte DataFrame a bytes de Excel."""
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Datos')
    return output.getvalue()


# ============================================
# ESTILOS
# ============================================

# Estilos inyectados globalmente via ui.inject_custom_css


# ============================================
# INTERFAZ
# ============================================

st.title("Reportes y Exportación")
st.markdown("*Genere reportes y respaldos del sistema*")

st.markdown("---")

# ============================================
# REPORTES DISPONIBLES
# ============================================

st.subheader("Reportes Disponibles")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div class="report-card">
        <div class="report-icon">📋</div>
        <h4>Reporte Maestro</h4>
        <p style="font-size: 0.85rem; color: #a0a0a0;">
            Todos los datos en formato institucional
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("� Generar Reporte Maestro", use_container_width=True, type="primary"):
        with st.spinner("Generando reporte..."):
            df = exportar_reporte_maestro()
            if not df.empty:
                excel = df_to_excel(df)
                st.download_button(
                    "⬇️ Descargar Excel",
                    data=excel,
                    file_name=f"Reporte_Maestro_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
                st.success(f"✅ Reporte generado: {len(df)} registros")

with col2:
    st.markdown("""
    <div class="report-card">
        <div class="report-icon">👥</div>
        <h4>Lista de Estudiantes</h4>
        <p style="font-size: 0.85rem; color: #a0a0a0;">
            Directorio completo de estudiantes
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("� Exportar Estudiantes", use_container_width=True):
        with st.spinner("Exportando..."):
            df = exportar_estudiantes_excel()
            if not df.empty:
                excel = df_to_excel(df)
                st.download_button(
                    "⬇️ Descargar Excel",
                    data=excel,
                    file_name=f"Estudiantes_{datetime.now().strftime('%Y%m%d')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
                st.success(f"✅ {len(df)} estudiantes exportados")

with col3:
    st.markdown("""
    <div class="report-card">
        <div class="report-icon">📜</div>
        <h4>Bitácora de Acciones</h4>
        <p style="font-size: 0.85rem; color: #a0a0a0;">
            Historial de operaciones del sistema
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("� Exportar Bitácora", use_container_width=True):
        with st.spinner("Exportando..."):
            df = exportar_bitacora()
            if not df.empty:
                excel = df_to_excel(df)
                st.download_button(
                    "⬇️ Descargar Excel",
                    data=excel,
                    file_name=f"Bitacora_{datetime.now().strftime('%Y%m%d')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
                st.success(f"✅ {len(df)} registros exportados")
            else:
                st.info("No hay registros en la bitácora")

st.markdown("---")

# ============================================
# RESPALDO DE BASE DE DATOS
# ============================================

st.subheader("Respaldo de Base de Datos")

col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("""
    ### Respaldo Completo
    
    Descargue una copia completa de la base de datos SQLite.
    Este archivo puede usarse para:
    
    - 🔄 Restaurar el sistema en caso de fallo
    - 📊 Análisis offline de datos
    - 🗄️ Archivo histórico
    """)
    
    config = get_config()
    db_path = Path(config.paths.db_path)
    
    if db_path.exists():
        tamaño = db_path.stat().st_size / 1024  # KB
        modificado = datetime.fromtimestamp(db_path.stat().st_mtime)
        
        st.info(f"📁 Base de datos: {db_path.name} ({tamaño:.1f} KB)")
        st.caption(f"Última modificación: {modificado.strftime('%d/%m/%Y %H:%M')}")
        
        with open(db_path, 'rb') as f:
            st.download_button(
                "💾 Descargar Respaldo BD",
                data=f.read(),
                file_name=f"sgte_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db",
                mime="application/octet-stream",
                type="primary"
            )
    else:
        st.warning("Base de datos no encontrada")

with col2:
    st.markdown("### 📅 Respaldos Automáticos")
    
    backup_path = Path(config.paths.backup_path)
    if backup_path.exists():
        backups = list(backup_path.glob("*.xlsx")) + list(backup_path.glob("*.db"))
        backups.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        if backups:
            st.caption(f"Últimos respaldos ({len(backups)} archivos):")
            for b in backups[:5]:
                st.text(f"📄 {b.name}")
        else:
            st.caption("No hay respaldos aún")
    else:
        st.caption("Carpeta de respaldos no configurada")

st.markdown("---")

# ============================================
# ESTADÍSTICAS DE USO
# ============================================

st.subheader("� Estadísticas del Sistema")

try:
    with get_session_context() as session:
        stats = {
            "Total Estudiantes": session.query(func.count(Estudiante.run)).scalar() or 0,
            "Total Proyectos": session.query(func.count(Proyecto.id)).scalar() or 0,
            "Documentos Cargados": session.query(func.count(Documento.id)).scalar() or 0,
            "Acciones en Bitácora": session.query(func.count(Bitacora.id)).scalar() or 0
        }
    
    cols = st.columns(4)
    for i, (label, value) in enumerate(stats.items()):
        with cols[i]:
            st.metric(label, value)

except Exception as e:
    st.error(f"Error obteniendo estadísticas: {e}")
