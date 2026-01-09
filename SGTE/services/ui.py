
"""
Servicio de UI - Gestión de estilos y componentes visuales
"""
import streamlit as st
from pathlib import Path


def inject_custom_css():
    """
    Inyecta TODOS los estilos CSS personalizados
    """
    # Cargar CSS principal
    css_file = Path(__file__).parent.parent / "assets" / "style.css"
    
    if css_file.exists():
        with open(css_file, "r", encoding="utf-8") as f:
            css_content = f.read()
            # Añadir CSS específico para ocultar navegación nativa y ajustar logo
            extra_css = """
            [data-testid="stSidebarNav"] { display: none !important; }
            .sidebar-logo-container { margin-top: auto; padding-bottom: 20px; text-align: center; }
            .sidebar-department-logo { max-width: 80%; opacity: 0.9; }
            """
            st.markdown(f"<style>{css_content}\n{extra_css}</style>", unsafe_allow_html=True)
    else:
        st.error(f"⚠️ No se encontró el archivo de estilos: {css_file}")
    
    # Cargar iconos de Boxicons
    st.markdown("""
        <link href='https://unpkg.com/boxicons@2.1.4/css/boxicons.min.css' rel='stylesheet'>
    """, unsafe_allow_html=True)


def render_global_sidebar(current_page="Inicio"):
    """
    Renderiza el sidebar global idéntico para todas las páginas.
    """
    with st.sidebar:
        # 1. Header (Solo Texto SGTE)
        st.markdown("""
            <style>
                /* FORZAR reducción de espacio superior en todo el sidebar */
                section[data-testid="stSidebar"] .block-container {
                    padding-top: 1rem !important;
                    padding-bottom: 0rem !important;
                }
                /* Hack adicional para versiones nuevas de Streamlit */
                div[data-testid="stSidebarUserContent"] {
                    padding-top: 0rem !important;
                }
            </style>
            <div style="padding: 0px 0 5px 0; text-align: center; margin-top: 0px;">
                <h1 style="color: #1a1a1a; font-size: 20px; font-weight: 900; letter-spacing: 0.5px; margin: 0; line-height: 1.2;">SGTE</h1>
                <p style="color: #888; font-size: 9px; margin-top: 0px; margin-bottom: 0px; text-transform: uppercase; letter-spacing: 1px; font-weight: 600;">Gestión de Titulaciones</p>
            </div>
            <hr style="margin: 10px 0 10px 0; border-color: rgba(0,0,0,0.05);">
        """, unsafe_allow_html=True)

        # 2. Navegación
        nav_items = {
            "Inicio": "Inicio.py",
            "Dashboard": "pages/1_Dashboard.py",
            "Estudiantes": "pages/2_Estudiantes.py",
            "Documentos": "pages/3_Documentos.py",
            "Operaciones Masivas": "pages/4_Operaciones_Masivas.py",
            "Reportes": "pages/5_Reportes.py",
            "PDF Splitter": "pages/6_PDF_Splitter.py"
        }

        for label, page_path in nav_items.items():
            # Estilo condicional si es la página actual
            is_active = (label == current_page)
            btn_kind = "primary" if is_active else "secondary"
            
            if st.button(label, key=f"nav_{label}", use_container_width=True, type=btn_kind):
                if not is_active:
                    st.switch_page(page_path)
        
        # 3. Espaciador y Logo del Departamento (Footer)
        # Usamos un contenedor vacío para empujar el logo al fondo si es necesario
        st.markdown("<div style='flex: 1;'></div>", unsafe_allow_html=True)
        
        # Logo del departamento
        logo_path = Path(__file__).parent.parent / "assets" / "logo_departamento.png"
        if logo_path.exists():
             st.image(str(logo_path), use_column_width=True)
        else:
             st.markdown("Departamento de Ingeniería Industrial")
             
        # Style hack para forzar flex column en sidebar
        st.markdown("""
            <style>
                [data-testid="stSidebar"] > div:first-child {
                    display: flex;
                    flex-direction: column;
                    height: 100vh;
                }
                [data-testid="stSidebar"] [data-testid="stImage"] {
                    margin-top: auto;
                    padding-bottom: 20px;
                }
            </style>
        """, unsafe_allow_html=True)


def render_hero(title: str, subtitle: str = "", icon: str = ""):
    """
    Renderiza un hero banner con gradiente
    """
    icon_html = f'<div style="font-size: 4rem; margin-bottom: 1rem;">{icon}</div>' if icon else ''
    
    st.markdown(f"""
        <div class="hero-container">
            {icon_html}
            <h1>{title}</h1>
            {f'<p>{subtitle}</p>' if subtitle else ''}
        </div>
    """, unsafe_allow_html=True)


def render_metric_card(label: str, value: str, icon: str = "", color: str = "primary"):
    """
    Renderiza una tarjeta de métrica personalizada
    """
    color_map = {
        "primary": "#17A499",
        "success": "#27AE60",
        "error": "#C0392B",
        "warning": "#F2994A",
        "info": "#2F80ED"
    }
    
    selected_color = color_map.get(color, color_map["primary"])
    
    st.markdown(f"""
        <div style="
            background-color: white;
            border: 1px solid #E1E5E5;
            border-radius: 12px;
            padding: 1.5rem;
            text-align: center;
            box-shadow: 0 2px 4px rgba(0,0,0,0.02);
            transition: transform 0.2s ease;
        ">
            <div style="font-size: 2rem; margin-bottom: 0.5rem;">{icon}</div>
            <div style="font-size: 2.5rem; font-weight: 700; color: {selected_color}; margin: 0.5rem 0;">
                {value}
            </div>
            <div style="color: #5F6B6A; font-size: 0.9rem; font-weight: 500;">
                {label}
            </div>
        </div>
    """, unsafe_allow_html=True)


def render_status_badge(status: str, text: str = None):
    """
    Renderiza un badge de estado
    """
    status_config = {
        "success": {"color": "#27AE60", "bg": "rgba(39, 174, 96, 0.1)", "icon": "✅"},
        "error": {"color": "#C0392B", "bg": "rgba(192, 57, 43, 0.1)", "icon": "❌"},
        "warning": {"color": "#F2994A", "bg": "rgba(242, 153, 74, 0.1)", "icon": "⚠️"},
        "info": {"color": "#2F80ED", "bg": "rgba(47, 128, 237, 0.1)", "icon": "ℹ️"},
        "pending": {"color": "#F2994A", "bg": "rgba(242, 153, 74, 0.1)", "icon": "⏳"}
    }
    
    config = status_config.get(status.lower(), status_config["info"])
    display_text = text or status.upper()
    
    st.markdown(f"""
        <span style="
            background-color: {config['bg']};
            color: {config['color']};
            padding: 0.25rem 0.75rem;
            border-radius: 12px;
            font-size: 0.85rem;
            font-weight: 600;
            display: inline-block;
        ">
            {config['icon']} {display_text}
        </span>
    """, unsafe_allow_html=True)


def render_card(content: str, title: str = None, variant: str = "default"):
    """
    Renderiza una tarjeta con contenido HTML
    """
    variant_styles = {
        "default": "background-color: white; border: 1px solid #E1E5E5;",
        "alt": "background-color: #F5F7F7; border: 1px solid #E1E5E5;",
        "success": "background-color: rgba(39, 174, 96, 0.05); border-left: 4px solid #27AE60;",
        "error": "background-color: rgba(192, 57, 43, 0.05); border-left: 4px solid #C0392B;",
        "warning": "background-color: rgba(242, 153, 74, 0.05); border-left: 4px solid #F2994A;"
    }
    
    style = variant_styles.get(variant, variant_styles["default"])
    title_html = f'<h4 style="margin-top: 0; color: #17A499;">{title}</h4>' if title else ''
    
    st.markdown(f"""
        <div style="{style} border-radius: 12px; padding: 1.5rem; margin: 1rem 0;">
            {title_html}
            {content}
        </div>
    """, unsafe_allow_html=True)
