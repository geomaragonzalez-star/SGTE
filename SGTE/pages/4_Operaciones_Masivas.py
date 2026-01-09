# pages/4_Operaciones_Masivas.py
"""
Tablero de Operaciones Masivas (RF-07).
Selección múltiple y ejecución de acciones en lote.
"""

import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Operaciones Masivas | SGTE", page_icon="📊", layout="wide")

from database import get_session_context, Estudiante, Proyecto, Expediente, EstadoExpediente
from services.estudiantes import buscar_estudiantes
from sqlalchemy import func
from services.ui import inject_custom_css, render_global_sidebar

# Inyectar estilos
inject_custom_css()
    
# Renderizar Sidebar Global
render_global_sidebar(current_page="Operaciones Masivas")


# ============================================
# FUNCIONES DE DATOS
# ============================================

def obtener_estudiantes_con_estado():
    """Obtiene estudiantes con su estado de expediente."""
    try:
        with get_session_context() as session:
            # Query con join
            resultados = session.query(
                Estudiante.run,
                Estudiante.nombres,
                Estudiante.apellidos,
                Estudiante.carrera,
                Expediente.estado
            ).outerjoin(
                Proyecto, Proyecto.estudiante_run == Estudiante.run
            ).outerjoin(
                Expediente, Expediente.proyecto_id == Proyecto.id
            ).all()
            
            return [{
                "seleccionar": False,
                "run": r.run,
                "nombre": f"{r.nombres} {r.apellidos}",
                "carrera": r.carrera,
                "estado": r.estado.value if r.estado else "sin_expediente"
            } for r in resultados]
    except Exception as e:
        st.error(f"Error: {e}")
        return []


def obtener_opciones_estado():
    """Retorna opciones de filtro por estado."""
    return [
        "Todos",
        "Sin Expediente",
        "Pendiente",
        "En Proceso", 
        "Listo para Envío",
        "Enviado"
    ]


# ============================================
# ESTILOS
# ============================================

# Estilos inyectados globalmente via ui.inject_custom_css


# ============================================
# ESTADO DE SESIÓN
# ============================================

if 'batch_selection' not in st.session_state:
    st.session_state.batch_selection = set()


# ============================================
# INTERFAZ
# ============================================

st.title("Operaciones Masivas")
st.markdown("*Seleccione múltiples estudiantes y ejecute acciones en lote*")

# ============================================
# FILTROS
# ============================================

st.markdown("---")
col1, col2, col3, col4 = st.columns([2, 2, 2, 1])

with col1:
    semestre = st.selectbox(
        "📅 Semestre",
        options=["Todos", "2026-1", "2025-2", "2025-1"],
        index=0
    )

with col2:
    estado_filtro = st.selectbox(
        "🚦 Estado",
        options=obtener_opciones_estado(),
        index=0
    )

with col3:
    busqueda = st.text_input("🔍 Buscar", placeholder="RUN o nombre...")

with col4:
    st.write("")
    st.write("")
    if st.button("�", help="Refrescar datos"):
        st.rerun()

st.markdown("---")

# ============================================
# TABLA CON SELECCIÓN
# ============================================

# Obtener datos
estudiantes = buscar_estudiantes(termino=busqueda if busqueda else None, limite=200)

if estudiantes:
    # Preparar DataFrame
    df = pd.DataFrame(estudiantes)
    df['seleccionar'] = False
    df = df[['seleccionar', 'run', 'nombres', 'apellidos', 'carrera']]
    df.columns = ['Seleccionar', 'RUN', 'Nombres', 'Apellidos', 'Carrera']
    
    # Editor de datos con checkboxes
    edited_df = st.data_editor(
        df,
        column_config={
            "Seleccionar": st.column_config.CheckboxColumn(
                "✓",
                help="Seleccionar para operación masiva",
                default=False
            ),
            "RUN": st.column_config.TextColumn("RUN", width="small"),
            "Carrera": st.column_config.TextColumn("Carrera", width="large")
        },
        hide_index=True,
        use_container_width=True,
        key="tabla_masiva"
    )
    
    # Obtener seleccionados
    seleccionados = edited_df[edited_df['Seleccionar'] == True]['RUN'].tolist()
    
    # ============================================
    # PANEL DE ACCIONES
    # ============================================
    
    st.markdown("---")
    
    # Contador
    col_counter, col_actions = st.columns([1, 4])
    
    with col_counter:
        st.markdown(f"""
        <div class="counter-badge">
            {len(seleccionados)} seleccionados
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Botones de acción
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        btn_memos = st.button(
            "📄 Generar Memos",
            type="primary",
            use_container_width=True,
            disabled=len(seleccionados) == 0
        )
    
    with col2:
        btn_emails = st.button(
            "📧 Enviar Correos",
            type="primary",
            use_container_width=True,
            disabled=len(seleccionados) == 0
        )
    
    with col3:
        btn_aprobar = st.button(
            "✅ Aprobar Hitos",
            use_container_width=True,
            disabled=len(seleccionados) == 0
        )
    
    with col4:
        btn_estado = st.button(
            "🔄 Cambiar Estado",
            use_container_width=True,
            disabled=len(seleccionados) == 0
        )
    
    with col5:
        btn_exportar = st.button(
            "📥 Exportar Lista",
            use_container_width=True,
            disabled=len(seleccionados) == 0
        )
    
    # ============================================
    # PROCESAMIENTO DE ACCIONES
    # ============================================
    
    if btn_memos and seleccionados:
        st.markdown("---")
        st.subheader("Generando Memorándums...")
        
        from services.memo_generator import generar_memorandums_masivo
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        def callback_memo(actual, total, run):
            progress_bar.progress(actual / total)
            status_text.text(f"Procesando {run}... ({actual}/{total})")
        
        try:
            zip_bytes, resultados = generar_memorandums_masivo(
                seleccionados,
                numero_memo_inicio=1,
                callback=callback_memo
            )
            
            exitosos = sum(1 for r in resultados if r.exito)
            fallidos = len(resultados) - exitosos
            
            progress_bar.progress(1.0)
            status_text.empty()
            
            if exitosos > 0:
                st.success(f"✅ {exitosos} memorándums generados correctamente")
                
                st.download_button(
                    "📥 Descargar ZIP con Memorándums",
                    data=zip_bytes,
                    file_name=f"memorandums_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
                    mime="application/zip",
                    type="primary"
                )
            
            if fallidos > 0:
                st.warning(f"⚠️ {fallidos} memorándums no pudieron generarse")
                with st.expander("Ver errores"):
                    for r in resultados:
                        if not r.exito:
                            st.error(f"{r.run}: {r.error}")
                            
        except Exception as e:
            st.error(f"Error: {e}")
    
    if btn_emails and seleccionados:
        st.markdown("---")
        st.subheader("� Cola de Envío de Correos")
        
        from services.email_queue import verificar_outlook, enviar_correos_masivo
        
        # Verificar Outlook primero
        outlook_ok, outlook_msg = verificar_outlook()
        
        if not outlook_ok:
            st.error(f"❌ {outlook_msg}")
            st.info("Asegúrese de que Microsoft Outlook esté instalado y abierto.")
        else:
            st.success("✅ Outlook disponible")
            st.warning("⚠️ Esta acción enviará correos reales a Registro Curricular")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                solo_borrador = st.checkbox("Solo guardar borradores", value=True)
            
            with col2:
                confirmar = st.button("Confirmar Envío", type="primary")
            
            with col3:
                if st.button("Cancelar"):
                    st.rerun()
            
            if confirmar:
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                def callback_email(actual, total, run):
                    progress_bar.progress(actual / total)
                    status_text.text(f"Enviando correo para {run}... ({actual}/{total})")
                
                try:
                    resultado = enviar_correos_masivo(
                        seleccionados,
                        callback=callback_email,
                        solo_borrador=solo_borrador
                    )
                    
                    progress_bar.progress(1.0)
                    status_text.empty()
                    
                    if resultado.exitosos > 0:
                        if solo_borrador:
                            st.success(f"✅ {resultado.exitosos} correos guardados en borradores")
                        else:
                            st.success(f"✅ {resultado.exitosos} correos enviados correctamente")
                    
                    if resultado.fallidos > 0:
                        st.warning(f"⚠️ {resultado.fallidos} correos fallaron")
                        with st.expander("Ver errores"):
                            for r in resultado.resultados:
                                if not r.exito:
                                    st.error(f"{r.run}: {r.mensaje}")
                    
                    if resultado.interrumpido:
                        st.error("Proceso interrumpido. Revise Outlook.")
                        
                except Exception as e:
                    st.error(f"Error: {e}")
    
    if btn_exportar and seleccionados:
        # Exportar seleccionados a Excel
        df_export = edited_df[edited_df['Seleccionar'] == True].drop(columns=['Seleccionar'])
        
        st.download_button(
            "📥 Descargar Excel",
            data=df_export.to_csv(index=False).encode('utf-8'),
            file_name=f"seleccion_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )

else:
    st.info("No hay estudiantes registrados.")

# ============================================
# INFORMACIÓN
# ============================================

with st.expander("ℹ️ Ayuda - Operaciones Masivas"):
    st.markdown("""
    ### Cómo usar este módulo
    
    1. **Filtrar**: Use los filtros superiores para encontrar los estudiantes deseados
    2. **Seleccionar**: Marque las casillas de los estudiantes a procesar
    3. **Ejecutar**: Presione el botón de la acción deseada
    
    ### Acciones disponibles
    
    - 📄 **Generar Memos**: Crea memorándums de apertura para los seleccionados
    - 📧 **Enviar Correos**: Envía solicitudes a Registro Curricular
    - ✅ **Aprobar Hitos**: Marca hitos como completados
    - 🔄 **Cambiar Estado**: Actualiza el estado del expediente
    - 📥 **Exportar Lista**: Descarga la selección en Excel
    
    ### Notas importantes
    
    - Los correos se envían con delay de 2 segundos para evitar bloqueos
    - Outlook debe estar abierto para el envío de correos
    - Se genera un log de todas las operaciones
    """)
