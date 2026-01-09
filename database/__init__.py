# database/__init__.py
"""
Módulo de persistencia de datos para SGTE.
Implementa SQLite con patrón de retry para resiliencia en red.
"""

from .connection import (
    get_engine, 
    get_session, 
    get_session_context,
    init_database,
    check_database_health,
    log_app_error,
    log_user_action
)

from .models import (
    Base,
    Estudiante,
    Proyecto,
    Comision,
    Expediente,
    Hito,
    Documento,
    Bitacora,
    AppLog,
    # Enums
    EstadoExpediente,
    ModalidadProyecto,
    TipoDocumento,
    TipoHito,
    NivelLog
)

__all__ = [
    # Connection
    "get_engine",
    "get_session",
    "get_session_context",
    "init_database",
    "check_database_health",
    "log_app_error",
    "log_user_action",
    # Models
    "Base",
    "Estudiante",
    "Proyecto",
    "Comision",
    "Expediente",
    "Hito",
    "Documento",
    "Bitacora",
    "AppLog",
    # Enums
    "EstadoExpediente",
    "ModalidadProyecto",
    "TipoDocumento",
    "TipoHito",
    "NivelLog"
]
