# services/__init__.py
"""
Módulo de servicios de negocio para SGTE.
Cada servicio implementa un Requisito Funcional específico.
"""

# RF-01: Gestión de Estudiantes
from .estudiantes import (
    crear_estudiante,
    obtener_estudiante,
    buscar_estudiantes,
    listar_estudiantes,
    actualizar_estudiante,
    eliminar_estudiante,
    obtener_carreras,
    contar_estudiantes,
    validar_run,
    formatear_run
)

# RF-03: PDF Splitter
from .pdf_splitter import (
    procesar_pdf_masivo,
    obtener_paginas_sin_asignar,
    detectar_run,
    HAS_PYMUPDF
)

# RF-04: Generador de Memorándums
from .memo_generator import (
    generar_memorandum,
    generar_memorandums_masivo,
    obtener_datos_estudiante
)

# RF-05: Cola de Correos
from .email_queue import (
    OutlookMailer,
    verificar_outlook,
    enviar_correos_masivo,
    OutlookNotInstalledException,
    OutlookBusyException
)

# RF-06: Exportación Excel
from .excel_export import (
    generar_reporte_maestro,
    guardar_backup_automatico,
    exportar_estudiantes,
    exportar_por_estado,
    obtener_datos_completos
)

__all__ = [
    # RF-01
    "crear_estudiante",
    "obtener_estudiante",
    "buscar_estudiantes",
    "listar_estudiantes",
    "actualizar_estudiante",
    "eliminar_estudiante",
    "obtener_carreras",
    "contar_estudiantes",
    "validar_run",
    "formatear_run",
    # RF-03
    "procesar_pdf_masivo",
    "obtener_paginas_sin_asignar",
    "detectar_run",
    "HAS_PYMUPDF",
    # RF-04
    "generar_memorandum",
    "generar_memorandums_masivo",
    "obtener_datos_estudiante",
    # RF-05
    "OutlookMailer",
    "verificar_outlook",
    "enviar_correos_masivo",
    "OutlookNotInstalledException",
    "OutlookBusyException",
    # RF-06
    "generar_reporte_maestro",
    "guardar_backup_automatico",
    "exportar_estudiantes",
    "exportar_por_estado",
    "obtener_datos_completos",
]
