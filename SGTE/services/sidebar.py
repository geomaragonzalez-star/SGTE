"""
Componente de Sidebar Moderno para SGTE
Inspirado en el diseño de constGenius
"""
import streamlit as st
from pathlib import Path


def render_modern_sidebar():
    """
    Renderiza un sidebar moderno con diseño colapsable
    """
    # Cargar CSS del sidebar
    sidebar_css = Path(__file__).parent.parent / "assets" / "sidebar.css"
    if sidebar_css.exists():
        with open(sidebar_css, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    
    # Inyectar iconos de Boxicons
    st.markdown("""
        <link href='https://unpkg.com/boxicons@2.1.4/css/boxicons.min.css' rel='stylesheet'>
    """, unsafe_allow_html=True)
    
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
        
        # Barra de búsqueda
        st.markdown("""
            <div class="sidebar-search">
                <i class='bx bx-search sidebar-search-icon'></i>
                <input type="text" placeholder="Buscar..." id="sidebar-search-input">
            </div>
        """, unsafe_allow_html=True)
        
        # Navegación principal
        st.markdown('<div class="sidebar-category">Principal</div>', unsafe_allow_html=True)
        
        # Items de navegación
        nav_items = [
            {"icon": "bx-grid-alt", "text": "Dashboard", "page": "pages/1_📋_Dashboard.py", "active": False},
            {"icon": "bx-user", "text": "Estudiantes", "page": "pages/2_👤_Estudiantes.py", "active": False},
            {"icon": "bx-file", "text": "Documentos", "page": "pages/3_📄_Documentos.py", "active": False},
        ]
        
        for item in nav_items:
            active_class = "active" if item["active"] else ""
            if st.button(
                f"{item['text']}", 
                key=f"nav_{item['text']}", 
                use_container_width=True,
                type="secondary"
            ):
                st.switch_page(item["page"])
        
        st.markdown('<div class="sidebar-category">Operaciones</div>', unsafe_allow_html=True)
        
        ops_items = [
            {"icon": "bx-bolt", "text": "Operaciones Masivas", "page": "pages/4_⚡_Operaciones_Masivas.py"},
            {"icon": "bx-bar-chart", "text": "Reportes", "page": "pages/5_📊_Reportes.py"},
            {"icon": "bx-file-blank", "text": "PDF Splitter", "page": "pages/6_📚_PDF_Splitter.py"},
        ]
        
        for item in ops_items:
            if st.button(
                f"{item['text']}", 
                key=f"nav_{item['text']}", 
                use_container_width=True,
                type="secondary"
            ):
                st.switch_page(item["page"])
        
        # Footer con perfil
        st.markdown("---")
        st.markdown("""
            <div class="sidebar-footer">
                <div class="sidebar-profile">
                    <div class="sidebar-profile-avatar">SD</div>
                    <div class="sidebar-profile-info">
                        <div class="sidebar-profile-name">Secretaría Docente</div>
                        <div class="sidebar-profile-role">Administrador</div>
                    </div>
                    <button class="sidebar-logout" title="Cerrar sesión">
                        <i class='bx bx-log-out'></i>
                    </button>
                </div>
            </div>
        """, unsafe_allow_html=True)


def render_custom_sidebar_html():
    """
    Renderiza un sidebar completamente personalizado con HTML/CSS/JS
    (Alternativa más avanzada)
    """
    st.markdown("""
    <style>
        /* Ocultar sidebar por defecto de Streamlit */
        [data-testid="stSidebar"][aria-expanded="true"] > div:first-child {
            width: 250px;
        }
        [data-testid="stSidebar"][aria-expanded="false"] > div:first-child {
            width: 250px;
            margin-left: -250px;
        }
    </style>
    
    <div class="custom-sidebar">
        <div class="sidebar-header">
            <div class="sidebar-logo">
                <div class="sidebar-logo-icon">🎓</div>
                <div class="sidebar-logo-text">SGTE</div>
            </div>
            <button class="sidebar-toggle" onclick="toggleSidebar()">
                <i class='bx bx-menu'></i>
            </button>
        </div>
        
        <div class="sidebar-search">
            <i class='bx bx-search sidebar-search-icon'></i>
            <input type="text" placeholder="Buscar...">
        </div>
        
        <nav class="sidebar-nav">
            <div class="sidebar-category">Principal</div>
            
            <div class="sidebar-nav-item">
                <a href="?page=dashboard" class="sidebar-nav-link active">
                    <i class='bx bx-grid-alt sidebar-nav-icon'></i>
                    <span class="sidebar-nav-text">Dashboard</span>
                </a>
                <span class="sidebar-tooltip">Dashboard</span>
            </div>
            
            <div class="sidebar-nav-item">
                <a href="?page=estudiantes" class="sidebar-nav-link">
                    <i class='bx bx-user sidebar-nav-icon'></i>
                    <span class="sidebar-nav-text">Estudiantes</span>
                </a>
                <span class="sidebar-tooltip">Estudiantes</span>
            </div>
            
            <div class="sidebar-nav-item">
                <a href="?page=documentos" class="sidebar-nav-link">
                    <i class='bx bx-file sidebar-nav-icon'></i>
                    <span class="sidebar-nav-text">Documentos</span>
                    <span class="sidebar-badge">3</span>
                </a>
                <span class="sidebar-tooltip">Documentos</span>
            </div>
            
            <div class="sidebar-category">Operaciones</div>
            
            <div class="sidebar-nav-item">
                <a href="?page=operaciones" class="sidebar-nav-link">
                    <i class='bx bx-bolt sidebar-nav-icon'></i>
                    <span class="sidebar-nav-text">Operaciones Masivas</span>
                </a>
                <span class="sidebar-tooltip">Operaciones Masivas</span>
            </div>
            
            <div class="sidebar-nav-item">
                <a href="?page=reportes" class="sidebar-nav-link">
                    <i class='bx bx-bar-chart sidebar-nav-icon'></i>
                    <span class="sidebar-nav-text">Reportes</span>
                </a>
                <span class="sidebar-tooltip">Reportes</span>
            </div>
            
            <div class="sidebar-nav-item">
                <a href="?page=pdf" class="sidebar-nav-link">
                    <i class='bx bx-file-blank sidebar-nav-icon'></i>
                    <span class="sidebar-nav-text">PDF Splitter</span>
                </a>
                <span class="sidebar-tooltip">PDF Splitter</span>
            </div>
            
            <div class="sidebar-category">Sistema</div>
            
            <div class="sidebar-nav-item">
                <a href="?page=settings" class="sidebar-nav-link">
                    <i class='bx bx-cog sidebar-nav-icon'></i>
                    <span class="sidebar-nav-text">Configuración</span>
                </a>
                <span class="sidebar-tooltip">Configuración</span>
            </div>
        </nav>
        
        <div class="sidebar-footer">
            <div class="sidebar-profile">
                <div class="sidebar-profile-avatar">SD</div>
                <div class="sidebar-profile-info">
                    <div class="sidebar-profile-name">Secretaría Docente</div>
                    <div class="sidebar-profile-role">Administrador</div>
                </div>
                <button class="sidebar-logout">
                    <i class='bx bx-log-out'></i>
                </button>
            </div>
        </div>
    </div>
    
    <script>
        function toggleSidebar() {
            const sidebar = document.querySelector('.custom-sidebar');
            sidebar.classList.toggle('collapsed');
        }
        
        // Manejar búsqueda
        const searchInput = document.querySelector('.sidebar-search input');
        searchInput.addEventListener('input', (e) => {
            const query = e.target.value.toLowerCase();
            const navItems = document.querySelectorAll('.sidebar-nav-item');
            
            navItems.forEach(item => {
                const text = item.querySelector('.sidebar-nav-text').textContent.toLowerCase();
                if (text.includes(query)) {
                    item.style.display = 'block';
                } else {
                    item.style.display = 'none';
                }
            });
        });
    </script>
    """, unsafe_allow_html=True)
