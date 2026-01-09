# pages/2_Estudiantes.py
"""
Gestión de Estudiantes - CRUD completo (RF-01).
Búsqueda por RUN/Nombre, formularios y validación.
"""

import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Estudiantes | SGTE", page_icon="📊", layout="wide")

from services.estudiantes import (
    crear_estudiante, obtener_estudiante, buscar_estudiantes,
    actualizar_estudiante, eliminar_estudiante, obtener_carreras,
    contar_estudiantes, validar_run, formatear_run
)
from services.ui import inject_custom_css, render_global_sidebar

# Inyectar estilos
inject_custom_css()
    
# Renderizar Sidebar Global
render_global_sidebar(current_page="Estudiantes")


# ============================================
# ESTILOS
# ============================================

# Estilos inyectados globalmente via ui.inject_custom_css


# ============================================
# ESTADO DE SESIÓN
# ============================================

if 'estudiante_seleccionado' not in st.session_state:
    st.session_state.estudiante_seleccionado = None
if 'modo_formulario' not in st.session_state:
    st.session_state.modo_formulario = None  # 'crear', 'editar', None


# ============================================
# FUNCIONES DE UI
# ============================================

def limpiar_seleccion():
    st.session_state.estudiante_seleccionado = None
    st.session_state.modo_formulario = None


def seleccionar_estudiante(run):
    st.session_state.estudiante_seleccionado = run
    st.session_state.modo_formulario = 'editar'


# ============================================
# INTERFAZ PRINCIPAL
# ============================================

st.title("Gestión de Estudiantes")

# Tabs principales
tab_lista, tab_nuevo = st.tabs(["Lista de Estudiantes", "Nuevo Estudiante"])


# ============================================
# TAB: LISTA DE ESTUDIANTES
# ============================================

with tab_lista:
    # Barra de búsqueda
    col_search, col_filter, col_count = st.columns([3, 2, 1])
    
    with col_search:
        termino_busqueda = st.text_input(
            "Buscar",
            placeholder="RUN o nombre del estudiante...",
            label_visibility="collapsed"
        )
    
    with col_filter:
        carreras = ["Todas"] + obtener_carreras()
        carrera_filtro = st.selectbox("Carrera", carreras, label_visibility="collapsed")
    
    # ============================================
    # LÓGICA DE DATOS OPTIMIZADA (CACHE)
    # ============================================

    @st.cache_data(ttl=300, show_spinner=False)
    def cargar_todos_estudiantes():
        from services.estudiantes import listar_estudiantes
        return listar_estudiantes(limite=5000)

    # Cargar datos (usando caché)
    todos_los_estudiantes = cargar_todos_estudiantes()
    
    # Convertir a DataFrame GLOBAL para filtrado rápido
    if todos_los_estudiantes:
        df_base = pd.DataFrame(todos_los_estudiantes)
    else:
        df_base = pd.DataFrame(columns=['run', 'nombres', 'apellidos', 'carrera', 'modalidad', 'nombre_completo'])

    # Lógica de Filtrado en Memoria (Pandas)
    df_filtrado = df_base.copy()

    if termino_busqueda:
        termino = termino_busqueda.lower()
        # Filtro multi-columna ignorando mayúsculas
        mask = (
            df_filtrado['run'].str.lower().str.contains(termino, na=False) | 
            df_filtrado['nombres'].str.lower().str.contains(termino, na=False) | 
            df_filtrado['apellidos'].str.lower().str.contains(termino, na=False)
        )
        df_filtrado = df_filtrado[mask]
    
    if carrera_filtro != "Todas":
        df_filtrado = df_filtrado[df_filtrado['carrera'] == carrera_filtro]

    # Actualizar métrica con el filtrado actual
    total = len(df_base)
    with col_count:
        st.metric("Total", total)
    
    # Mostrar Resultados
    if not df_filtrado.empty:
        # Preparar DF para visualización
        df_show = df_filtrado[['run', 'nombres', 'apellidos', 'carrera', 'modalidad']].copy()
        df_show.columns = ['RUN', 'Nombres', 'Apellidos', 'Carrera', 'Modalidad']
        
        # Tabla Principal
        st.dataframe(
            df_show,
            use_container_width=True,
            hide_index=True,
            column_config={
                "RUN": st.column_config.TextColumn("RUN", width="small"),
                "Modalidad": st.column_config.TextColumn("Modalidad", width="small")
            }
        )
        
        # Selector para edición (usando los datos filtrados)
        st.markdown("---")
        col1, col2 = st.columns([3, 1])
        
        # Lista de diccionarios para el selectbox
        opciones_estudiantes = df_filtrado.to_dict('records')
        
        with col1:
            run_seleccionado = st.selectbox(
                "Seleccionar estudiante para editar",
                options=[e['run'] for e in opciones_estudiantes],
                format_func=lambda x: f"{x} - {next((e['nombre_completo'] for e in opciones_estudiantes if e['run'] == x), '')}"
            )
        
        with col2:
            if st.button("Editar", use_container_width=True, type="primary"):
                seleccionar_estudiante(run_seleccionado)
                st.rerun()

    else:
        if not df_base.empty:
            st.info(f"No hay coincidencias para '{termino_busqueda}'.")
        else:
            st.info("No hay estudiantes registrados. Use el tab 'Nuevo Estudiante' para agregar.")

    # ============================================
    # PANEL DE EDICIÓN (si hay selección)
    # ============================================
    
    if st.session_state.modo_formulario == 'editar' and st.session_state.estudiante_seleccionado:
        st.markdown("---")
        st.subheader("Editar Estudiante")
        
        est = obtener_estudiante(st.session_state.estudiante_seleccionado)
        
        if est:
            with st.form("form_editar"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.text_input("RUN", value=est.run, disabled=True)
                    nombres = st.text_input("Nombres", value=est.nombres)
                    apellidos = st.text_input("Apellidos", value=est.apellidos)
                
                with col2:
                    carrera = st.text_input("Carrera", value=est.carrera)
                    modalidad = st.selectbox("Modalidad", ["Diurno", "Vespertino", "Online"], index=["Diurno", "Vespertino", "Online"].index(est.modalidad) if est.modalidad in ["Diurno", "Vespertino", "Online"] else 0)
                
                col_save, col_delete, col_cancel = st.columns(3)
                
                with col_save:
                    guardar = st.form_submit_button("Guardar", type="primary", use_container_width=True)
                
                with col_delete:
                    confirmar_eliminar = st.form_submit_button("Eliminar", use_container_width=True)
                
                with col_cancel:
                    cancelar = st.form_submit_button("Cancelar", use_container_width=True)
                
                if guardar:
                    exito, msg = actualizar_estudiante(
                        est.run,
                        {"nombres": nombres, "apellidos": apellidos, "carrera": carrera, "modalidad": modalidad}
                    )
                    if exito:
                        st.success(msg)
                        cargar_todos_estudiantes.clear() # Invalidar caché
                        limpiar_seleccion()
                        st.rerun()
                    else:
                        st.error(msg)
                
                if confirmar_eliminar:
                    exito, msg = eliminar_estudiante(est.run)
                    if exito:
                        st.success(msg)
                        cargar_todos_estudiantes.clear() # Invalidar caché
                        limpiar_seleccion()
                        st.rerun()
                    else:
                        st.error(msg)
                
                if cancelar:
                    limpiar_seleccion()
                    st.rerun()


# ============================================
# TAB: NUEVO ESTUDIANTE
# ============================================

with tab_nuevo:
    st.subheader("Registrar Nuevo Estudiante")
    
    with st.form("form_crear", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            run = st.text_input(
                "RUN *",
                placeholder="Ej: 12.345.678-9",
                help="Ingrese el RUN con o sin puntos y guión"
            )
            nombres = st.text_input("Nombres *", placeholder="Ej: Juan Pablo")
            apellidos = st.text_input("Apellidos *", placeholder="Ej: González Pérez")
        
        with col2:
            carrera = st.text_input(
                "Carrera *",
                placeholder="Ej: Ingeniería Civil en Informática"
            )
            modalidad = st.selectbox(
                "Modalidad *",
                ["Diurno", "Vespertino", "Online"]
            )
        
        # Validación en tiempo real del RUN
        if run:
            valido, msg = validar_run(run)
            if valido:
                st.success(f"RUN válido: {formatear_run(run)}")
            else:
                st.warning(f"{msg}")
        
        submitted = st.form_submit_button("Crear Estudiante", type="primary", use_container_width=True)
        
        if submitted:
            if not all([run, nombres, apellidos, carrera]):
                st.error("Complete todos los campos obligatorios (*)")
            else:
                exito, msg, estudiante = crear_estudiante(
                    run=run,
                    nombres=nombres,
                    apellidos=apellidos,
                    carrera=carrera,
                    modalidad=modalidad
                )
                
                if exito:
                    st.success(f"{msg}")
                    cargar_todos_estudiantes.clear() # Invalidar caché
                    st.balloons()
                else:
                    st.error(f"{msg}")
    
    # Información adicional
    with st.expander("Información sobre el RUN"):
        st.markdown("""
        - El RUN (Rol Único Nacional) es el identificador único de cada estudiante
        - Puede ingresarlo con o sin puntos y guión
        - El sistema validará automáticamente el dígito verificador
        - Ejemplos válidos: `12.345.678-9`, `12345678-9`, `123456789`
        """)
