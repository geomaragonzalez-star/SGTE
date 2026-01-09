# pages/1_Dashboard.py
"""
Dashboard Principal - Vista general del sistema SGTE.
Implementa RF-07 (Tablero) y RFN-01 (Semáforos de estado).
"""

import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Dashboard | SGTE", page_icon="📊", layout="wide")

# Imports
from database import get_session_context, Estudiante, Proyecto, Expediente, EstadoExpediente
from services.estudiantes import contar_estudiantes
from services.ui import inject_custom_css, render_global_sidebar, render_hero, render_metric_card, render_status_badge
from sqlalchemy import func

# Inyectar estilos
inject_custom_css()
    
# Renderizar Sidebar Global
render_global_sidebar(current_page="Dashboard")


# ============================================
# FUNCIONES DE DATOS
# ============================================

@st.cache_data(ttl=60)
def obtener_metricas():
    """Obtiene métricas generales del sistema."""
    try:
        with get_session_context() as session:
            total_estudiantes = session.query(func.count(Estudiante.run)).scalar() or 0
            total_proyectos = session.query(func.count(Proyecto.id)).scalar() or 0
            
            # Contar por estado de expediente
            pendientes = session.query(func.count(Expediente.id)).filter(
                Expediente.estado == EstadoExpediente.PENDIENTE
            ).scalar() or 0
            
            en_proceso = session.query(func.count(Expediente.id)).filter(
                Expediente.estado == EstadoExpediente.EN_PROCESO
            ).scalar() or 0
            
            listos = session.query(func.count(Expediente.id)).filter(
                Expediente.estado == EstadoExpediente.LISTO_ENVIO
            ).scalar() or 0
            
            enviados = session.query(func.count(Expediente.id)).filter(
                Expediente.estado == EstadoExpediente.ENVIADO
            ).scalar() or 0
            
            titulados = session.query(func.count(Expediente.id)).filter(
                Expediente.titulado == True
            ).scalar() or 0
            
            return {
                "total_estudiantes": total_estudiantes,
                "total_proyectos": total_proyectos,
                "pendientes": pendientes,
                "en_proceso": en_proceso,
                "listos": listos,
                "enviados": enviados,
                "titulados": titulados
            }
    except Exception as e:
        st.error(f"Error obteniendo métricas: {e}")
        return {k: 0 for k in ["total_estudiantes", "total_proyectos", "pendientes", 
                               "en_proceso", "listos", "enviados", "titulados"]}


@st.cache_data(ttl=60)
def obtener_distribucion_carreras():
    """Obtiene distribución de estudiantes por carrera."""
    try:
        with get_session_context() as session:
            resultado = session.query(
                Estudiante.carrera,
                func.count(Estudiante.run).label('cantidad')
            ).group_by(Estudiante.carrera).all()
            
            return pd.DataFrame(resultado, columns=['Carrera', 'Cantidad'])
    except Exception as e:
        return pd.DataFrame()


@st.cache_data(ttl=60)
def obtener_ultimos_registros(limite=10):
    """Obtiene los últimos estudiantes registrados."""
    try:
        with get_session_context() as session:
            estudiantes = session.query(Estudiante).order_by(
                Estudiante.created_at.desc()
            ).limit(limite).all()
            
            return [{
                "RUN": e.run,
                "Nombre": e.nombre_completo,
                "Carrera": e.carrera,
                "Registrado": e.created_at.strftime("%d/%m/%Y %H:%M") if e.created_at else "-"
            } for e in estudiantes]
    except Exception as e:
        return []


# ============================================
# ESTILOS
# ============================================

# Estilos inyectados globalmente via ui.inject_custom_css


# ============================================
# INTERFAZ
# ============================================

st.title("Dashboard")
st.markdown(f"*Actualizado: {datetime.now().strftime('%d/%m/%Y %H:%M')}*")

# Botón refrescar
col_refresh, _ = st.columns([1, 5])
with col_refresh:
    if st.button("Actualizar", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

st.markdown("---")

# Obtener métricas
metricas = obtener_metricas()

# ============================================
# MÉTRICAS PRINCIPALES
# ============================================

st.subheader("Resumen General")

col1, col2, col3, col4 = st.columns(4)

with col1:
    render_metric_card(
        label="Total Estudiantes",
        value=str(metricas['total_estudiantes']),
        icon="",
        color="primary"
    )

with col2:
    render_metric_card(
        label="Proyectos Activos",
        value=str(metricas['total_proyectos']),
        icon="",
        color="info"
    )

with col3:
    render_metric_card(
        label="Enviados a Registro",
        value=str(metricas['enviados']),
        icon="",
        color="success"
    )

with col4:
    render_metric_card(
        label="Titulados",
        value=str(metricas['titulados']),
        icon="",
        color="primary"
    )

st.markdown("<br>", unsafe_allow_html=True)

# ============================================
# SEMÁFORO DE ESTADOS
# ============================================

st.subheader("Estado de Expedientes")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
    <div class="section-alt" style="border-left: 4px solid #C0392B;">
        <h3 style="margin:0; color:#C0392B;">{metricas['pendientes']}</h3>
        <p style="margin:0.5rem 0 0 0; color: #5F6B6A;">Pendientes</p>
        <small style="color: #5F6B6A;">Falta documentación</small>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="section-alt" style="border-left: 4px solid #F2994A;">
        <h3 style="margin:0; color:#F2994A;">{metricas['en_proceso']}</h3>
        <p style="margin:0.5rem 0 0 0; color: #5F6B6A;">En Proceso</p>
        <small style="color: #5F6B6A;">Validando documentos</small>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="section-alt" style="border-left: 4px solid #27AE60;">
        <h3 style="margin:0; color:#27AE60;">{metricas['listos']}</h3>
        <p style="margin:0.5rem 0 0 0; color: #5F6B6A;">Listos para Envío</p>
        <small style="color: #5F6B6A;">Documentación completa</small>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class="section-alt" style="border-left: 4px solid #2F80ED;">
        <h3 style="margin:0; color:#2F80ED;">{metricas['enviados']}</h3>
        <p style="margin:0.5rem 0 0 0; color: #5F6B6A;">Enviados</p>
        <small style="color: #5F6B6A;">En Registro Curricular</small>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# ============================================
# SECCIONES ADICIONALES
# ============================================

col_left, col_right = st.columns(2)

with col_left:
    st.subheader("Distribución por Carrera")
    df_carreras = obtener_distribucion_carreras()
    if not df_carreras.empty:
        st.bar_chart(df_carreras.set_index('Carrera'))
    else:
        st.info("Sin datos de carreras aún.")

with col_right:
    st.subheader("Últimos Registros")
    ultimos = obtener_ultimos_registros()
    if ultimos:
        st.dataframe(
            pd.DataFrame(ultimos),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No hay estudiantes registrados.")

# ============================================
# ACCIONES RÁPIDAS
# ============================================

st.markdown("---")
st.subheader("Acciones Rápidas")

col1, col2, col3, col4 = st.columns(4)

with col1:
    if st.button("Nuevo Estudiante", use_container_width=True, type="primary"):
        st.switch_page("pages/2_Estudiantes.py")

with col2:
    if st.button("Cargar Documentos", use_container_width=True):
        st.switch_page("pages/3_Documentos.py")

with col3:
    if st.button("Operaciones Masivas", use_container_width=True):
        st.switch_page("pages/4_Operaciones_Masivas.py")

with col4:
    if st.button("Generar Reportes", use_container_width=True):
        st.switch_page("pages/5_Reportes.py")
