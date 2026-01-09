# app.py
"""
SGTE - Sistema de Gestión de Titulaciones y Expedientes
Punto de entrada principal de la aplicación Streamlit.
"""

import streamlit as st
from pathlib import Path
from loguru import logger

# Configuración de página (debe ser la primera llamada de Streamlit)
st.set_page_config(
    page_title="SGTE - Gestión de Titulaciones",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'About': "### SGTE v2.0\nSistema de Gestión de Titulaciones y Expedientes"
    }
)

# Imports del proyecto
from config import get_config
from database import init_database, check_database_health
from services.ui import inject_custom_css, render_hero, render_metric_card


# ============================================
# INICIALIZACIÓN
# ============================================

def init_session_state():
    """Inicializa variables de estado de sesión."""
    defaults = {
        'selected_student': None,
        'upload_queue': [],
        'processing_status': {
            'is_running': False,
            'current_task': None,
            'progress': 0,
            'total': 0,
            'errors': []
        },
        'filters': {
            'semestre': 'Todos',
            'estado': 'Todos',
            'carrera': 'Todas'
        },
        'batch_selection': set(),
        'db_initialized': False
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def init_app():
    """Inicializa la aplicación y la base de datos."""
    config = get_config()
    config.ensure_directories()
    
    if not st.session_state.get('db_initialized'):
        with st.spinner("Inicializando base de datos..."):
            if init_database():
                st.session_state['db_initialized'] = True
                logger.info("Base de datos inicializada correctamente")
            else:
                st.error("❌ Error inicializando la base de datos")
                st.stop()


# ============================================
# PÁGINA PRINCIPAL
# ============================================

def main():
    """Función principal de la aplicación."""
    init_session_state()
    init_app()
    
    # Inyectar estilos CSS personalizados
    inject_custom_css()
    
    # Sidebar moderno
    with st.sidebar:
        # Header del sidebar
        st.markdown("""
            <div class="sidebar-header">
                <div class="sidebar-logo">
                    <div class="sidebar-logo-icon">🎓</div>
                    <div class="sidebar-logo-text">SGTE</div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Navegación principal
        st.markdown('<div class="sidebar-category">PRINCIPAL</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns([1, 4])
        with col1:
            st.markdown('<i class="bx bx-grid-alt" style="font-size: 20px; color: #17A499;"></i>', unsafe_allow_html=True)
        with col2:
            st.markdown("**Dashboard**")
        
        st.markdown('<div class="sidebar-category">GESTIÓN</div>', unsafe_allow_html=True)
        
        # Estudiantes
        col1, col2 = st.columns([1, 4])
        with col1:
            st.markdown('<i class="bx bx-user" style="font-size: 20px; color: rgba(255,255,255,0.7);"></i>', unsafe_allow_html=True)
        with col2:
            if st.button("Estudiantes", key="nav_estudiantes", use_container_width=True):
                st.switch_page("pages/2_👤_Estudiantes.py")
        
        # Documentos
        col1, col2 = st.columns([1, 4])
        with col1:
            st.markdown('<i class="bx bx-file" style="font-size: 20px; color: rgba(255,255,255,0.7);"></i>', unsafe_allow_html=True)
        with col2:
            if st.button("Documentos", key="nav_docs", use_container_width=True):
                st.switch_page("pages/3_📄_Documentos.py")
        
        st.markdown('<div class="sidebar-category">OPERACIONES</div>', unsafe_allow_html=True)
        
        # Operaciones Masivas
        col1, col2 = st.columns([1, 4])
        with col1:
            st.markdown('<i class="bx bx-bolt" style="font-size: 20px; color: rgba(255,255,255,0.7);"></i>', unsafe_allow_html=True)
        with col2:
            if st.button("Operaciones", key="nav_ops", use_container_width=True):
                st.switch_page("pages/4_⚡_Operaciones_Masivas.py")
        
        # Reportes
        col1, col2 = st.columns([1, 4])
        with col1:
            st.markdown('<i class="bx bx-bar-chart" style="font-size: 20px; color: rgba(255,255,255,0.7);"></i>', unsafe_allow_html=True)
        with col2:
            if st.button("Reportes", key="nav_reports", use_container_width=True):
                st.switch_page("pages/5_📊_Reportes.py")
        
        # PDF Splitter
        col1, col2 = st.columns([1, 4])
        with col1:
            st.markdown('<i class="bx bx-file-blank" style="font-size: 20px; color: rgba(255,255,255,0.7);"></i>', unsafe_allow_html=True)
        with col2:
            if st.button("PDF Splitter", key="nav_pdf", use_container_width=True):
                st.switch_page("pages/6_📚_PDF_Splitter.py")
        
        st.markdown("---")
        
        # Estado de BD
        health = check_database_health()
        if health["status"] == "healthy":
            st.success("✅ BD Conectada")
        else:
            st.error(f"❌ Error BD")
        
        st.markdown("---")
        
        # Footer con perfil
        st.markdown("""
            <div class="sidebar-footer">
                <div class="sidebar-profile">
                    <div class="sidebar-profile-avatar">SD</div>
                    <div class="sidebar-profile-info">
                        <div class="sidebar-profile-name">Secretaría Docente</div>
                        <div class="sidebar-profile-role">USACH</div>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)
    
    # Hero principal
    render_hero(
        title="Sistema de Gestión de Titulaciones",
        subtitle="Gestione expedientes, documentos y procesos de titulación de forma eficiente",
        icon="🎓"
    )
    
    # Métricas rápidas
    st.markdown("### 📊 Resumen Rápido")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        render_metric_card(
            label="Pendientes",
            value="0",
            icon="📋",
            color="warning"
        )
    
    with col2:
        render_metric_card(
            label="En Proceso",
            value="0",
            icon="⏳",
            color="info"
        )
    
    with col3:
        render_metric_card(
            label="Listos",
            value="0",
            icon="✅",
            color="success"
        )
    
    with col4:
        render_metric_card(
            label="Titulados",
            value="0",
            icon="🎓",
            color="primary"
        )
    
    st.markdown("---")
    
    # Accesos rápidos
    st.markdown("### ⚡ Accesos Rápidos")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
            <div class="section-alt">
                <h4 style="color: #17A499; margin-top: 0;">👤 Estudiantes</h4>
                <p style="color: #5F6B6A; font-size: 0.9rem;">
                    Gestione el registro y datos de estudiantes
                </p>
            </div>
        """, unsafe_allow_html=True)
        if st.button("Ir a Estudiantes", use_container_width=True, type="primary"):
            st.switch_page("pages/2_👤_Estudiantes.py")
    
    with col2:
        st.markdown("""
            <div class="section-alt">
                <h4 style="color: #17A499; margin-top: 0;">📄 Documentos</h4>
                <p style="color: #5F6B6A; font-size: 0.9rem;">
                    Valide y gestione documentos habilitantes
                </p>
            </div>
        """, unsafe_allow_html=True)
        if st.button("Ir a Documentos", use_container_width=True, type="primary"):
            st.switch_page("pages/3_📄_Documentos.py")
    
    with col3:
        st.markdown("""
            <div class="section-alt">
                <h4 style="color: #17A499; margin-top: 0;">⚡ Operaciones</h4>
                <p style="color: #5F6B6A; font-size: 0.9rem;">
                    Procesos masivos y automatización
                </p>
            </div>
        """, unsafe_allow_html=True)
        if st.button("Ir a Operaciones", use_container_width=True, type="primary"):
            st.switch_page("pages/4_⚡_Operaciones_Masivas.py")
    
    st.markdown("---")
    
    # Información del sistema
    st.markdown("### ℹ️ Estado del Sistema")
    
    col1, col2 = st.columns(2)
    
    with col1:
        config = get_config()
        st.markdown("""
            <div class="section-alt">
                <h4 style="color: #17A499; margin-top: 0;">⚙️ Configuración</h4>
            </div>
        """, unsafe_allow_html=True)
        st.json({
            "Base de datos": str(config.paths.db_path),
            "Expedientes": str(config.paths.expedientes_root),
            "Modo debug": config.app.debug_mode,
            "Versión": config.app.version
        })
    
    with col2:
        st.markdown("""
            <div class="section-alt">
                <h4 style="color: #17A499; margin-top: 0;">💾 Base de Datos</h4>
            </div>
        """, unsafe_allow_html=True)
        st.json(health)
    
    # Footer
    st.markdown("---")
    st.caption("SGTE v2.0 | Secretaría Docente | Universidad de Santiago de Chile | 2026")


if __name__ == "__main__":
    main()
