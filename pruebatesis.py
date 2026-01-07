"""
Sistema de Gestión - Departamento de Industrias
Universidad de Santiago de Chile
"""

import sys
import os
import re
import zipfile
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Tuple, Optional, Any
from PySide6.QtWidgets import QGraphicsDropShadowEffect
from PySide6.QtCore import QFileSystemWatcher

try:
    from PySide6.QtWidgets import *
    from PySide6.QtCore import Qt, QThread, Signal, QTimer, QSize
    from PySide6.QtGui import QFont, QColor, QIcon, QPixmap, QPalette
except ImportError:
    print("Error: PySide6 no está instalado.")
    print("Ejecute: pip install PySide6 openpyxl PyMuPDF pdf2image pytesseract")
    sys.exit(1)

try:
    import pandas as pd
except ImportError:
    print("Error: pandas no está instalado.")
    print("Ejecute: pip install pandas")
    sys.exit(1)

from word_utils import WordTemplate, fecha_larga_hoy
from date_utils import fecha_larga_es
import win32com.client
import pythoncom
from data_service import (
    get_excel_path, set_excel_path, load_students_df,
    get_drive_root_dir, get_students_base_dir, CANON_COLS
)

# ============================================================================
# CONFIGURACIÓN Y CONSTANTES
# ============================================================================

HEADERS = {
    "nombre_completo": "Nombre Completo",
    "rut": "RUT",
    "carrera": "Carrera",
    "modalidad": "Modalidad",
    "semestre": "Semestre",
    "titulo_proyecto": "Título Proyecto",
    "profesor_guia": "Profesor Guía",
    "corrector1": "Corrector 1",
    "corrector2": "Corrector 2",
    "fecha_examen": "Fecha Examen",
    "sala": "Sala",
    "estado_constancias": "Constancias"
}

THRESHOLD_BACKLOG_DAYS = 30

class Config:
    """Configuración global de la aplicación"""
    
    CARPETAS_ESTUDIANTE = [
        "bienestar", "biblioteca", "SDT", "finanzas", "memorandum"
    ]
    
    # Paleta de colores institucional
    COLORS = {
        'primary': '#0aac9c',
        'secondary': '#16aca4',
        'accent': '#f15500',
        'gray': '#82888d',
        'light': '#d1c7bf',
        'white': '#FFFFFF',
        'text': '#2c3e50',
        'hover': '#089187',
        'border': '#e0e0e0',
    }
    
    # Espaciado
    SPACING = {
        'xs': '4px',
        'sm': '8px',
        'md': '16px',
        'lg': '24px',
        'xl': '32px'
    }
    
    # Tipos de trámites
    TRAMITES = [
        'Finanzas',
        'Bienestar',
        'Biblioteca', 
        'SDT',
        'Memorandum'
    ]
    
    # Configuración de la interfaz
    WINDOW_TITLE = "SIGETI (Sistema de Gestión de Titulación Industrial)"
    FONT_FAMILY = "Segoe UI"
    FONT_SIZE = 10

# ============================================================================
# ESTILOS DE LA INTERFAZ
# ============================================================================

STYLE = f"""
/* Estilo Global */
QMainWindow {{
    background-color: #f8f9fa;
}}

QWidget {{
    font-family: '{Config.FONT_FAMILY}';
    font-size: {Config.FONT_SIZE}pt;
    color: {Config.COLORS['text']};
}}

/* Barra de Navegación */
#navbar {{
    background-color: {Config.COLORS['primary']};
    border-radius: 8px;
    margin: {Config.SPACING['sm']};
    padding: 8px 12px;  /* Ajustar padding vertical */
    min-height: 50px;   /* Altura mínima para englobar tabs */
}}

#navbar QPushButton {{
    background-color: transparent;
    color: {Config.COLORS['white']};
    border: none;
    border-radius: 6px;
    padding: 12px 24px;
    font-size: 11pt;
    font-weight: bold;
}}

#navbar QPushButton:hover {{
    background-color: {Config.COLORS['hover']};
}}

#navbar QPushButton:checked {{
    background-color: {Config.COLORS['secondary']};
    border-bottom: 3px solid {Config.COLORS['accent']};
}}

/* Título de la aplicación */
#appTitleLabel {{
    color: {Config.COLORS['white']};
    font-size: 16px;
    font-weight: bold;
    padding-right: 20px;
}}

/* Contenedores y Tarjetas */
QGroupBox {{
    background-color: {Config.COLORS['white']};
    border: 1px solid {Config.COLORS['border']};
    border-radius: 10px;
    margin-top: {Config.SPACING['lg']};
    padding: {Config.SPACING['md']};
    font-weight: bold;
}}

QGroupBox::title {{
    color: {Config.COLORS['text']};
    subcontrol-origin: margin;
    left: {Config.SPACING['md']};
    padding: 0 {Config.SPACING['sm']};
}}

/* Tarjetas KPI */
#kpiCard {{
    background-color: {Config.COLORS['light']};
    border-radius: 10px;
    padding: {Config.SPACING['md']};
    margin: {Config.SPACING['sm']};
}}

#kpiTitle {{
    color: {Config.COLORS['text']};
    font-size: 12pt;
    font-weight: bold;
    margin-bottom: {Config.SPACING['sm']};
}}

#kpiValue {{
    color: {Config.COLORS['primary']};
    font-size: 24pt;
    font-weight: bold;
}}

/* Tarjetas de estadísticas */
#statCard {{
    background-color: {Config.COLORS['white']};
    border-radius: 12px;
    border: 1px solid {Config.COLORS['border']};
}}

#statTitle {{
    color: {Config.COLORS['gray']};
    font-size: 14pt;
    font-weight: bold;
    margin-bottom: 10px;
}}

#statValue {{
    color: {Config.COLORS['primary']};
    font-size: 24pt;
    font-weight: bold;
}}

/* Tabla */
QTableWidget {{
    border: 1px solid {Config.COLORS['border']};
    border-radius: 8px;
    background: {Config.COLORS['white']};
    gridline-color: {Config.COLORS['border']};
    padding: {Config.SPACING['sm']};
}}

QHeaderView::section {{
    background-color: {Config.COLORS['secondary']};
    color: {Config.COLORS['white']};
    padding: 8px;
    border: none;
    font-weight: bold;
}}

QTableWidget::item {{
    padding: {Config.SPACING['sm']};
}}

QTableWidget::item:selected {{
    background-color: {Config.COLORS['primary']};
    color: {Config.COLORS['white']};
}}

/* Botones y Controles */
QPushButton {{
    background-color: {Config.COLORS['primary']};
    color: {Config.COLORS['white']};
    border: none;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: bold;
}}

QPushButton:hover {{
    background-color: {Config.COLORS['hover']};
}}

/* Otros widgets */
QLineEdit, QComboBox {{
    border: 2px solid {Config.COLORS['border']};
    border-radius: 6px;
    padding: 8px;
    background-color: {Config.COLORS['white']};
}}

QLineEdit:focus, QComboBox:focus {{
    border-color: {Config.COLORS['primary']};
}}
"""

# ============================================================================
# HELPERS
# ============================================================================

def docs_ok_for_student(nombre: str, rut: str) -> Tuple[bool, int]:
    """
    Verifica si alumno tiene al menos 1 PDF en cada carpeta requerida.
    Retorna (completo: bool, carpetas_faltantes: int)
    """
    try:
        base_dir = get_students_base_dir()
        root = base_dir / f"{nombre}_{rut}"
        required = ["bienestar", "biblioteca", "SDT", "finanzas"]
        missing = 0
        for sub in required:
            p = root / sub
            ok = p.exists() and any(ch.suffix.lower() == ".pdf" for ch in p.iterdir() if ch.is_file())
            if not ok:
                missing += 1
        return (missing == 0, missing)
    except Exception:
        return (False, len(["bienestar", "biblioteca", "SDT", "finanzas"]))

# ============================================================================
# CLASES PRINCIPALES
# ============================================================================

class ProcessWorker(QThread):
    """Worker thread para procesamiento asíncrono"""
    progress = Signal(int, str)
    finished = Signal(list)
    error = Signal(str)
    
    def __init__(self, file_path: str, tipo_tramite: str):
        super().__init__()
        self.file_path = file_path
        self.tipo_tramite = tipo_tramite
        
    def run(self):
        try:
            # Aquí iría la lógica de procesamiento real
            # Simulación de procesamiento (en producción aquí iría el OCR real)
            for i, estudiante in enumerate(ESTUDIANTES_DUMMY):
                self.progress.emit(
                    int((i + 1) / len(ESTUDIANTES_DUMMY) * 100),
                    f"Procesando: {estudiante['nombre']}"
                )
                self.msleep(800)  # Simular procesamiento
                
            self.finished.emit([])
            
        except Exception as e:
            self.error.emit(str(e))

class StatCard(QFrame):
    """Widget reutilizable para tarjetas de estadísticas"""
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.setObjectName("statCard")
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        self.setMaximumHeight(160)  # Altura fija para las tarjetas
        
        # Agregar sombra
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(10)
        shadow.setXOffset(0)
        shadow.setYOffset(2)
        shadow.setColor(QColor(0, 0, 0, 30))
        self.setGraphicsEffect(shadow)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # Título
        self.title_label = QLabel(title)
        self.title_label.setObjectName("statTitle")
        layout.addWidget(self.title_label)
        
        # Valor
        self.value_label = QLabel()
        self.value_label.setObjectName("statValue")
        self.value_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.value_label)
        
    def set_value(self, text: str):
        """Establece el valor a mostrar"""
        self.value_label.setText(text)

class MemoWorker(QThread):
    """Worker thread para generar memorándums"""
    progress = Signal(int, str)
    finished = Signal(bool, str, int)
    
    def __init__(self, estudiantes: List[Dict], template_path: Path, parent=None):
        super().__init__(parent)
        self.estudiantes = estudiantes
        self.template_path = template_path
        
    def run(self):
        try:
            word = WordTemplate()
            total = len(self.estudiantes)
            
            for i, estudiante in enumerate(self.estudiantes):
                self.progress.emit(
                    int((i + 1) / total * 100),
                    f"Generando memorándum para {estudiante['nombre']}..."
                )
                
                # Obtener base_dir dinámicamente desde data_service
                base_dir = get_students_base_dir()
                nombre_carpeta = f"{estudiante['nombre']}_{estudiante['rut']}"
                student_dir = base_dir / nombre_carpeta / "memorandum"
                student_dir.mkdir(parents=True, exist_ok=True)
                
                fecha = datetime.now().strftime("%Y%m%d")
                pdf_path = student_dir / f"Memorandum_{nombre_carpeta}_{fecha}.pdf"
                
                # Valores para los bookmarks
                replacements = {
                    "NOMBRE_ESTUDIANTE": estudiante['nombre'],
                    "RUT": estudiante['rut'],
                    "CARRERA": estudiante['carrera'],
                    "MODALIDAD": estudiante['modalidad'],
                    "FECHA_HOY": fecha_larga_hoy()
                }
                
                word.generate_pdf(self.template_path, pdf_path, replacements)
            
            word.close()
            base_dir_str = str(get_students_base_dir())
            self.finished.emit(True, base_dir_str, total)
            
        except Exception as e:
            self.finished.emit(False, str(e), 0)

class SuccessDialog(QDialog):
    """Diálogo personalizado para mensaje de éxito"""
    def __init__(self, message: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Proceso Completado")
        self.setFixedWidth(400)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Icono + Mensaje
        msg_layout = QHBoxLayout()
        icon_label = QLabel()
        icon_label.setPixmap(QApplication.style().standardIcon(
            QStyle.SP_DialogApplyButton).pixmap(32, 32))
        msg_layout.addWidget(icon_label)
        
        text_label = QLabel(message)
        text_label.setWordWrap(True)
        msg_layout.addWidget(text_label, stretch=1)
        layout.addLayout(msg_layout)
        
        # Botón OK
        btn_ok = QPushButton("OK")
        btn_ok.setFixedWidth(100)
        btn_ok.clicked.connect(self.accept)
        layout.addWidget(btn_ok, alignment=Qt.AlignCenter)
        
        # Estilo
        self.setStyleSheet(f"""
            QDialog {{
                background-color: white;
            }}
            QLabel {{
                color: {Config.COLORS['text']};
                font-size: 11pt;
            }}
            QPushButton {{
                background-color: {Config.COLORS['primary']};
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {Config.COLORS['hover']};
            }}
        """)

# -----------------------
# StatsService - funciones helper (stub / placeholders)
# -----------------------
def get_total_students(estudiantes: List[Dict], semestre: Optional[str]=None, carrera: Optional[str]=None, search: Optional[str]=None) -> int:
    """Retorna total de estudiantes aplicando filtros (stub)."""
    filtered = []
    for e in estudiantes:
        ok = True
        if semestre and 'semestre' in e and e['semestre'] != semestre:
            ok = False
        if carrera and e.get('carrera') != carrera:
            ok = False
        if search:
            s = search.lower()
            if s not in e.get('nombre','').lower() and s not in e.get('rut','').lower():
                ok = False
        if ok:
            filtered.append(e)
    return len(filtered)

def get_modality_distribution(estudiantes: List[Dict], semestre: Optional[str]=None, carrera: Optional[str]=None, search: Optional[str]=None) -> Dict[str, float]:
    """Retorna distribución por modalidad (porcentaje)."""
    total = get_total_students(estudiantes, semestre, carrera, search)
    if total == 0:
        return {}
    counts = {}
    for e in estudiantes:
        ok = True
        if semestre and 'semestre' in e and e['semestre'] != semestre:
            ok = False
        if carrera and e.get('carrera') != carrera:
            ok = False
        if search:
            s = search.lower()
            if s not in e.get('nombre','').lower() and s not in e.get('rut','').lower():
                ok = False
        if not ok:
            continue
        mod = e.get('modalidad','Desconocida')
        counts[mod] = counts.get(mod, 0) + 1
    return {k: v/total*100 for k, v in counts.items()}

def get_project_stats(estudiantes: List[Dict], **kwargs) -> Dict[str, Any]:
    """Stub: retorna % con proyecto y % con comisión completa"""
    # TODO: Conectar con BD / DataFrame real
    total = get_total_students(estudiantes, kwargs.get('semestre'), kwargs.get('carrera'), kwargs.get('search'))
    if total == 0:
        return {'pct_with_project': 0.0, 'pct_with_full_commission': 0.0}
    # dummy: supongamos 60% con proyecto, 40% con comisión completa
    return {'pct_with_project': 60.0, 'pct_with_full_commission': 40.0}

def get_documents_stats(estudiantes: List[Dict], **kwargs) -> Dict[str, Any]:
    """Stub: retorna % constancias completas y n pendientes"""
    total = get_total_students(estudiantes, kwargs.get('semestre'), kwargs.get('carrera'), kwargs.get('search'))
    if total == 0:
        return {'pct_complete': 0.0, 'n_pending': 0}
    # dummy values
    return {'pct_complete': 72.0, 'n_pending': int(total * 0.28)}

def get_schedule_stats(estudiantes: List[Dict], **kwargs) -> Dict[str, Any]:
    """Stub: retorna agenda stats"""
    # dummy
    return {'scheduled': 10, 'pending': 5, 'progress_pct': 66.0}

def get_backlog_stats(estudiantes: List[Dict], **kwargs) -> Dict[str, Any]:
    """Stub: backlog small card"""
    return {'avg_wait_days': 18, 'n_over_threshold': 3}

# ============================================================================
# CLASES PRINCIPALES
# ============================================================================

class MainWindow(QMainWindow):
    """Ventana principal de la aplicación"""
    
    def __init__(self):
        super().__init__()
        self.estudiantes = []
        self.df_actual = pd.DataFrame()  # Almacena el DF actual
        try:
            self.BASE_DIR = get_students_base_dir()
        except FileNotFoundError:
            self.BASE_DIR = None
        self.init_ui()
        self.cargar_datos_demo()
        
    def init_ui(self):
        """Inicializa la interfaz de usuario"""
        self.setWindowTitle(Config.WINDOW_TITLE)
        self.setStyleSheet(STYLE)
        
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        
        self.create_navbar(layout)
        
        self.stack = QStackedWidget()
        self.init_pages()
        layout.addWidget(self.stack)
        
        self.worker = None
        
        # File System Watcher para monitorear cambios en Excel
        self.fs_watcher = QFileSystemWatcher(self)
        self._rearm_excel_watcher()

    def _rearm_excel_watcher(self):
        """Reengancha el file watcher al Excel actual."""
        try:
            self.fs_watcher.blockSignals(True)
            files = self.fs_watcher.files()
            if files:
                self.fs_watcher.removePaths(files)
            p = get_excel_path()
            if p and p.exists():
                self.fs_watcher.addPath(str(p))
        finally:
            self.fs_watcher.blockSignals(False)
        self.fs_watcher.fileChanged.connect(self._on_excel_changed)

    def _on_excel_changed(self, _path):
        """Callback cuando el Excel cambia en Drive."""
        QTimer.singleShot(800, self.reload_data)

    def init_pages(self):
        """Inicializa las páginas del sistema"""
        self.home_page = self.create_home_page()
        self.stack.addWidget(self.home_page)
        
        self.docs_page = self.create_docs_page()
        self.stack.addWidget(self.docs_page)
        
        self.memo_page = self.create_memo_page()
        self.stack.addWidget(self.memo_page)

    def create_navbar(self, layout: QVBoxLayout):
        """Crea la barra de navegación con título"""
        navbar = QWidget()
        navbar.setObjectName("navbar")
        nav_layout = QHBoxLayout(navbar)
        nav_layout.setContentsMargins(10, 0, 10, 0)
        nav_layout.setSpacing(15)
        
        self.nav_buttons = []
        pages = ["Inicio", "Gestión Documentos", "Memorandums"]
        
        for text in pages:
            btn = QPushButton(text)
            btn.setCheckable(True)
            btn.clicked.connect(lambda c, x=len(self.nav_buttons): 
                              self.change_page(x))
            nav_layout.addWidget(btn)
            self.nav_buttons.append(btn)
        
        nav_layout.addStretch()
        
        title_label = QLabel("SIGETI")
        title_label.setObjectName("appTitleLabel")
        nav_layout.addWidget(title_label)
        
        layout.addWidget(navbar)
        self.nav_buttons[0].setChecked(True)

    def change_page(self, index: int):
        """Cambia la página activa"""
        self.stack.setCurrentIndex(index)
        for i, btn in enumerate(self.nav_buttons):
            btn.setChecked(i == index)

    def create_home_page(self) -> QWidget:
        """Dashboard: izquierda tabla (65%), derecha KPIs + próximos (35%)"""
        page = QWidget()
        main_layout = QHBoxLayout(page)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(16)
        
        # Columna izquierda (tabla + filtros)
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(10)
        
        # Filtros
        filters_widget = QWidget()
        filters_layout = QHBoxLayout(filters_widget)
        filters_layout.setContentsMargins(0, 0, 0, 0)
        filters_layout.setSpacing(10)
        
        filters_layout.addWidget(QLabel("Buscar:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar por RUT o nombre...")
        filters_layout.addWidget(self.search_input)
        
        filters_layout.addWidget(QLabel("Carrera:"))
        self.carrera_filter = QComboBox()
        self.carrera_filter.addItem("Todas")
        filters_layout.addWidget(self.carrera_filter)
        
        filters_layout.addWidget(QLabel("Semestre:"))
        self.semestre_filter = QComboBox()
        self.semestre_filter.addItem("Todas")
        self.semestre_filter.addItems(["2025-1", "2025-2", "2024-2"])
        filters_layout.addWidget(self.semestre_filter)

        self.btn_reload = QPushButton("Actualizar datos")
        self.btn_reload.setToolTip("Recargar datos desde el Excel configurado")
        self.btn_reload.clicked.connect(self.reload_data)
        filters_layout.addWidget(self.btn_reload)

        self.btn_change_excel = QPushButton("Cambiar Excel…")
        self.btn_change_excel.setToolTip("Seleccionar otro archivo Excel en Google Drive")
        self.btn_change_excel.clicked.connect(self.change_excel)
        filters_layout.addWidget(self.btn_change_excel)

        left_layout.addWidget(filters_widget)
        
        # Tabla con columnas canónicas
        self.tabla_estudiantes = QTableWidget()
        self.tabla_estudiantes.setColumnCount(len(CANON_COLS))
        headers = [HEADERS.get(c, c) for c in CANON_COLS]
        self.tabla_estudiantes.setHorizontalHeaderLabels(headers)
        
        header = self.tabla_estudiantes.horizontalHeader()
        for i, col in enumerate(CANON_COLS):
            if col in ["nombre_completo", "titulo_proyecto"]:
                header.setSectionResizeMode(i, QHeaderView.Stretch)
            elif col in ["rut", "sala", "fecha_examen"]:
                header.setSectionResizeMode(i, QHeaderView.ResizeToContents)
            else:
                header.setSectionResizeMode(i, QHeaderView.ResizeToContents)
        
        left_layout.addWidget(self.tabla_estudiantes)
        
        # Conectar filtros
        self.search_input.textChanged.connect(self.refresh_home_view)
        self.carrera_filter.currentTextChanged.connect(self.refresh_home_view)
        self.semestre_filter.currentTextChanged.connect(self.refresh_home_view)

        # Columna derecha (KPIs + próximos exámenes)
        right = QWidget()
        right.setMaximumWidth(420)
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(12)
        
        self.card_total = StatCard("Total Estudiantes")
        self.card_modalidad = StatCard("Distribución por Modalidad")
        self.card_project = StatCard("Estado de Proyectos")
        self.card_docs = StatCard("Estado Documentación")
        self.card_schedule = StatCard("Agenda de Exámenes")
        self.card_backlog = StatCard("Backlog de Agenda")
        
        right_layout.addWidget(self.card_total)
        right_layout.addWidget(self.card_modalidad)
        right_layout.addWidget(self.card_project)
        right_layout.addWidget(self.card_docs)
        right_layout.addWidget(self.card_schedule)
        right_layout.addWidget(self.card_backlog)
        
        # Mini listado: Próximos exámenes
        prox_group = QGroupBox("Próximos Exámenes (5)")
        prox_layout = QVBoxLayout(prox_group)
        prox_layout.setContentsMargins(8, 8, 8, 8)
        prox_layout.setSpacing(6)
        
        self.tabla_proximos = QTableWidget()
        self.tabla_proximos.setColumnCount(2)
        self.tabla_proximos.setHorizontalHeaderLabels(["Fecha", "Alumno"])
        self.tabla_proximos.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.tabla_proximos.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.tabla_proximos.setMaximumHeight(150)
        prox_layout.addWidget(self.tabla_proximos)
        
        right_layout.addWidget(prox_group)
        right_layout.addStretch()
        
        main_layout.addWidget(left, stretch=65)
        main_layout.addWidget(right, stretch=35)
        
        self.refresh_home_view()
        
        return page

    def reload_data(self):
        """Carga el Excel y actualiza vistas."""
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            semester = self.semestre_filter.currentText() if hasattr(self, 'semestre_filter') else None
            if semester == "Todas":
                semester = None
            
            self.df_actual = load_students_df(semester)
            
            # Convertir DF a lista de dicts para compatibilidad
            self.estudiantes = self.df_actual.to_dict('records')
            self.BASE_DIR = get_students_base_dir()
            
            # Poblar combos
            carreras = sorted({e.get('carrera', '') for e in self.estudiantes if e.get('carrera')})
            self.carrera_filter.blockSignals(True)
            self.carrera_filter.clear()
            self.carrera_filter.addItem("Todas")
            for c in carreras:
                self.carrera_filter.addItem(c)
            self.carrera_filter.blockSignals(False)
            
            if 'semestre' in self.df_actual.columns:
                sems = sorted({str(s).strip() for s in self.df_actual['semestre'].dropna().unique() if s})
                self.semestre_filter.blockSignals(True)
                self.semestre_filter.clear()
                self.semestre_filter.addItem("Todas")
                for s in sems:
                    self.semestre_filter.addItem(s)
                self.semestre_filter.blockSignals(False)
            
            self.refresh_home_view()
            self.actualizar_tabla_memos()
            QMessageBox.information(self, "Datos cargados", "Los datos se han actualizado correctamente desde el Excel.")
            
            # Reenganchar watcher después de carga exitosa
            self._rearm_excel_watcher()
            
        except FileNotFoundError as ex:
            QMessageBox.critical(self, "Archivo no encontrado", f"No se encontró el Excel:\n{ex}")
        except Exception as ex:
            QMessageBox.critical(self, "Error al cargar datos", f"Ocurrió un error al leer el Excel:\n{ex}")
        finally:
            QApplication.restoreOverrideCursor()

    def change_excel(self):
        """Permite al usuario seleccionar otro archivo Excel."""
        try:
            suggested = get_drive_root_dir()
        except FileNotFoundError:
            suggested = Path("G:/Mi unidad/SIGETI")
        
        start_dir = str(suggested) if suggested.exists() else str(Path.home())

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar archivo Excel",
            start_dir,
            "Archivos Excel (*.xlsx *.xlsm)"
        )
        if not file_path:
            return
        p = Path(file_path)
        try:
            set_excel_path(p)
            self.reload_data()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo cargar el Excel seleccionado:\n{e}")

    def cargar_datos_demo(self):
        """Carga datos inicialmente."""
        excel_path = get_excel_path()
        if not excel_path:
            suggested = Path("G:/Mi unidad/SIGETI/alumnos.xlsx")
            start_dir = str(Path("G:/Mi unidad/SIGETI")) if Path("G:/Mi unidad/SIGETI").exists() else str(Path.home())
            
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Seleccionar archivo Excel de datos",
                start_dir,
                "Archivos Excel (*.xlsx *.xlsm)"
            )
            if not file_path:
                QMessageBox.warning(self, "Ruta no configurada", "Se usarán datos de demostración.")
                self.estudiantes = [
                    {
                        'nombre_completo': 'Ana González',
                        'rut': '12.345.678-9',
                        'carrera': 'Ingeniería Civil Industrial',
                        'modalidad': 'Diurno',
                        'semestre': '2025-1',
                        'titulo_proyecto': 'Proyecto Demo',
                        'profesor_guia': 'Dr. Pérez',
                        'corrector1': 'Dr. García',
                        'corrector2': 'Dr. López',
                        'fecha_examen': '',
                        'sala': '',
                        'estado_constancias': ''
                    }
                ]
                try:
                    self.BASE_DIR = get_students_base_dir()
                except FileNotFoundError:
                    self.BASE_DIR = Path("G:/Mi unidad/SIGETI/Estudiantes")
                self.refresh_home_view()
                self.actualizar_tabla_memos()
                return
            
            set_excel_path(Path(file_path))
        
        try:
            self.reload_data()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"No se pudo cargar datos: {e}\nUsando demostración.")
            self.estudiantes = [
                {
                    'nombre_completo': 'Ana González',
                    'rut': '12.345.678-9',
                    'carrera': 'Ingeniería Civil Industrial',
                    'modalidad': 'Diurno',
                    'semestre': '2025-1',
                    'titulo_proyecto': 'Proyecto Demo',
                    'profesor_guia': 'Dr. Pérez',
                    'corrector1': 'Dr. García',
                    'corrector2': 'Dr. López',
                    'fecha_examen': '',
                    'sala': '',
                    'estado_constancias': ''
                }
            ]
            try:
                self.BASE_DIR = get_students_base_dir()
            except FileNotFoundError:
                self.BASE_DIR = Path("G:/Mi unidad/SIGETI/Estudiantes")
            self.refresh_home_view()
            self.actualizar_tabla_memos()

    def refresh_home_view(self):
        """Actualiza tabla y KPIs con filtros aplicados."""
        try:
            semestre = self.semestre_filter.currentText()
            carrera = self.carrera_filter.currentText()
            search = self.search_input.text().lower()
            
            # Filtrar DF
            filtered_df = self.df_actual.copy()
            
            if semestre and semestre != "Todas":
                filtered_df = filtered_df[filtered_df['semestre'] == semestre]
            
            if carrera and carrera != "Todas":
                filtered_df = filtered_df[filtered_df['carrera'] == carrera]
            
            if search:
                mask = (
                    filtered_df['nombre_completo'].str.lower().str.contains(search, na=False) |
                    filtered_df['rut'].str.lower().str.contains(search, na=False)
                )
                filtered_df = filtered_df[mask]
            
            # Actualizar tabla
            self.tabla_estudiantes.setRowCount(0)
            for _, row in filtered_df.iterrows():
                row_pos = self.tabla_estudiantes.rowCount()
                self.tabla_estudiantes.insertRow(row_pos)
                for col_idx, col_name in enumerate(CANON_COLS):
                    val = str(row.get(col_name, ''))
                    self.tabla_estudiantes.setItem(row_pos, col_idx, QTableWidgetItem(val))
            
            # Actualizar KPIs reales
            self._update_kpis(filtered_df)
            
            # Actualizar tabla de próximos exámenes
            self._update_upcoming_exams(filtered_df)
            
        except Exception as e:
            QMessageBox.critical(self, "Error al actualizar vista", str(e))

    def _update_kpis(self, df: pd.DataFrame):
        """Actualiza KPIs basados en DF filtrado."""
        total = len(df)
        
        # Total Estudiantes
        self.card_total.set_value(str(total))
        
        # Distribución por Modalidad
        if total > 0:
            mod_counts = df['modalidad'].value_counts()
            mod_pct = (mod_counts / total * 100).round(1)
            mod_text = ", ".join([f"{k}: {v}%" for k, v in mod_pct.items()])
            self.card_modalidad.set_value(mod_text if mod_text else "Sin datos")
        else:
            self.card_modalidad.set_value("Sin datos")
        
        # Estado de Proyectos
        if total > 0:
            proj_count = len(df[(df['titulo_proyecto'] != '') & (df['titulo_proyecto'].notna())])
            comision_count = len(df[
                (df['profesor_guia'] != '') & (df['profesor_guia'].notna()) &
                (df['corrector1'] != '') & (df['corrector1'].notna()) &
                (df['corrector2'] != '') & (df['corrector2'].notna())
            ])
            proj_pct = proj_count / total * 100
            comision_pct = comision_count / total * 100
            self.card_project.set_value(f"Proyecto: {proj_pct:.1f}% | Comisión: {comision_pct:.1f}%")
        else:
            self.card_project.set_value("Sin datos")
        
        # Estado de Documentación / Constancias
        if total > 0:
            if 'estado_constancias' in df.columns and (df['estado_constancias'] != '').any():
                complete = len(df[df['estado_constancias'].str.lower() == 'completo'])
            else:
                # Inferir desde filesystem
                complete = 0
                for _, row in df.iterrows():
                    ok, _ = docs_ok_for_student(row['nombre_completo'], row['rut'])
                    if ok:
                        complete += 1
            
            complete_pct = complete / total * 100
            pending = total - complete
            self.card_docs.set_value(f"Completas: {complete_pct:.1f}% | Pendientes: {pending}")
        else:
            self.card_docs.set_value("Sin datos")
        
        # Agenda de Exámenes
        if total > 0 and 'fecha_examen' in df.columns:
            scheduled = len(df[(df['fecha_examen'] != '') & (df['fecha_examen'].notna())])
            pending = total - scheduled
            progress = scheduled / total * 100 if total > 0 else 0
            self.card_schedule.set_value(f"Agendados: {scheduled} | Pendientes: {pending} | Avance: {progress:.1f}%")
        else:
            self.card_schedule.set_value("Sin datos")
        
        # Backlog de Agenda
        # Para simplificar: calcular promedio de días pendientes si existen fechas
        self.card_backlog.set_value("s/i")  # sin información

    def _update_upcoming_exams(self, df: pd.DataFrame):
        """Actualiza tabla de próximos 5 exámenes."""
        self.tabla_proximos.setRowCount(0)
        
        try:
            if 'fecha_examen' not in df.columns or df.empty:
                return
            
            # Filtrar fechas válidas
            df_exams = df[(df['fecha_examen'] != '') & (df['fecha_examen'].notna())].copy()
            if df_exams.empty:
                return
            
            # Convertir a datetime si no lo son
            try:
                df_exams['fecha_examen'] = pd.to_datetime(df_exams['fecha_examen'])
            except Exception:
                return
            
            # Filtrar >= hoy, ordenar, tomar 5
            today = pd.Timestamp.today().normalize()
            df_exams = df_exams[df_exams['fecha_examen'] >= today].sort_values('fecha_examen').head(5)
            
            for _, row in df_exams.iterrows():
                fecha_str = pd.Timestamp(row['fecha_examen']).strftime("%d/%m/%Y")
                nombre = row['nombre_completo']
                
                row_pos = self.tabla_proximos.rowCount()
                self.tabla_proximos.insertRow(row_pos)
                self.tabla_proximos.setItem(row_pos, 0, QTableWidgetItem(fecha_str))
                self.tabla_proximos.setItem(row_pos, 1, QTableWidgetItem(nombre))
        
        except Exception:
            pass  # Ignorar errores de parseo de fechas

    def create_docs_page(self) -> QWidget:
        """Página para gestión de documentos"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)
        
        title_label = QLabel("Gestión de Documentos")
        title_label.setObjectName("appTitleLabel")
        layout.addWidget(title_label)
        
        instructions = QLabel("Suba aquí los documentos (ZIP o PDF) de los estudiantes.")
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        self.status_container = QGroupBox("Estado de Carga")
        self.status_container.setObjectName("statusContainer")
        self.status_layout = QVBoxLayout(self.status_container)
        self.status_layout.setContentsMargins(10, 10, 10, 10)
        self.status_layout.setSpacing(8)
        layout.addWidget(self.status_container)
        
        self.status_table = QTableWidget()
        self.status_table.setColumnCount(4)
        self.status_table.setHorizontalHeaderLabels([
            "Nombre Archivo", "Estado", "Progreso", "Mensaje"
        ])
        header = self.status_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        self.status_layout.addWidget(self.status_table)
        
        self.btn_process_docs = QPushButton("Procesar Documentos")
        self.btn_process_docs.setObjectName("btnProcessDocs")
        self.btn_process_docs.setFixedHeight(40)
        self.btn_process_docs.clicked.connect(self.process_documents)
        layout.addWidget(self.btn_process_docs, alignment=Qt.AlignRight)
        
        return page

    def open_selected_student_folder(self):
        """Abre carpeta del alumno seleccionado"""
        try:
            table = getattr(self, 'tabla_estudiantes', None)
            if not table:
                return
            selected = table.selectedItems()
            if not selected:
                QMessageBox.information(self, "Seleccionar alumno", "Seleccione un alumno en la tabla para abrir su carpeta.")
                return
            row = selected[0].row()
            nombre = table.item(row, 0).text()
            rut = table.item(row, 1).text()
            
            base_dir = get_students_base_dir()
            student_dir = base_dir / f"{nombre}_{rut}"
            
            if (student_dir / "memorandum").exists():
                target = student_dir / "memorandum"
            else:
                target = student_dir
            
            try:
                os.startfile(str(target))
            except Exception:
                QMessageBox.warning(self, "No se pudo abrir", f"No se pudo abrir la carpeta:\n{target}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al abrir carpeta: {e}")

    def create_memo_page(self) -> QWidget:
        """Página para generación de memorándums"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)
        
        title_label = QLabel("Generación de Memorándums")
        title_label.setObjectName("appTitleLabel")
        layout.addWidget(title_label)
        
        instructions = QLabel("Seleccione a los estudiantes y genere los memorándums.")
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        # Tabla con columnas canónicas (mismo que Inicio)
        self.tabla_memos = QTableWidget()
        self.tabla_memos.setColumnCount(len(CANON_COLS))
        headers = [HEADERS.get(c, c) for c in CANON_COLS]
        self.tabla_memos.setHorizontalHeaderLabels(headers)
        
        header = self.tabla_memos.horizontalHeader()
        for i, col in enumerate(CANON_COLS):
            if col in ["nombre_completo", "titulo_proyecto"]:
                header.setSectionResizeMode(i, QHeaderView.Stretch)
            else:
                header.setSectionResizeMode(i, QHeaderView.ResizeToContents)
        
        layout.addWidget(self.tabla_memos)
        
        layout.addStretch()
        
        btn_layout = QHBoxLayout()
        self.btn_generate_memos = QPushButton("Generar Memorándums")
        self.btn_generate_memos.setObjectName("btnGenerateMemos")
        self.btn_generate_memos.setFixedHeight(40)
        self.btn_generate_memos.clicked.connect(self.generate_memos)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_generate_memos)
        
        layout.addLayout(btn_layout)
        
        return page

    def actualizar_tabla_memos(self):
        """Actualiza tabla de memorándums con todas las columnas canónicas."""
        try:
            self.tabla_memos.setRowCount(0)
            
            for est in self.estudiantes:
                row_pos = self.tabla_memos.rowCount()
                self.tabla_memos.insertRow(row_pos)
                for col_idx, col_name in enumerate(CANON_COLS):
                    val = str(est.get(col_name, ''))
                    self.tabla_memos.setItem(row_pos, col_idx, QTableWidgetItem(val))
        
        except Exception as e:
            QMessageBox.critical(self, "Error al actualizar memorándums", str(e))

    def get_selected_students(self) -> List[Dict]:
        """Obtiene estudiantes seleccionados desde tabla de memorándums."""
        selected = []
        for row in range(self.tabla_memos.rowCount()):
            if self.tabla_memos.item(row, 0).isSelected():
                est_dict = {}
                for col_idx, col_name in enumerate(CANON_COLS):
                    val = self.tabla_memos.item(row, col_idx).text()
                    est_dict[col_name] = val
                selected.append(est_dict)
        return selected

    def generate_memos(self):
        """Generar memorándums para estudiantes seleccionados"""
        try:
            estudiantes = self.get_selected_students()
            if not estudiantes:
                QMessageBox.warning(self, "Sin selección", "Seleccione al menos un estudiante.")
                return
            
            template_path, _ = QFileDialog.getOpenFileName(
                self,
                "Seleccionar plantilla de memorándum",
                str(get_drive_root_dir()),
                "Archivos de Word (*.docx)"
            )
            if not template_path:
                return
            template_path = Path(template_path)
            
            if not template_path.is_file():
                QMessageBox.critical(self, "Error", "Plantilla no válida.")
                return
            
            self.btn_generate_memos.setEnabled(False)
            
            self.worker = MemoWorker(estudiantes, template_path)
            self.worker.progress.connect(self.update_memo_progress)
            self.worker.finished.connect(self.memos_generation_finished)
            self.worker.start()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def update_memo_progress(self, pct: int, message: str):
        """Actualizar progreso"""
        pass

    def memos_generation_finished(self, success: bool, message: str, total: int):
        """Finalizar generación"""
        if success:
            QMessageBox.information(
                self, 
                "Éxito", 
                f"Se generaron {total} memorándums.\nCarpeta base: {message}"
            )
        else:
            QMessageBox.critical(self, "Error", f"No se pudieron generar:\n{message}")
        
        self.btn_generate_memos.setEnabled(True)

    def process_documents(self):
        """Placeholder"""
        QMessageBox.information(self, "Función", "En desarrollo.")

# ============================================================================
# PUNTO DE ENTRADA
# ============================================================================

def main():
    """Función principal"""
    app = QApplication(sys.argv)
    
    font = QFont(Config.FONT_FAMILY, Config.FONT_SIZE)
    app.setFont(font)
    
    window = MainWindow()
    window.show()
    QTimer.singleShot(100, window.showMaximized)
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
