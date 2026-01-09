# database/connection.py
"""
Módulo de conexión a base de datos SQLite con patrón de retry.
Diseñado para ser resiliente a bloqueos en entornos de red compartida.
"""

import sqlite3
from pathlib import Path
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.engine import Engine
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log
)
from loguru import logger
import streamlit as st

from .models import Base


# ============================================
# CONFIGURACIÓN DESDE SECRETS
# ============================================

def _get_db_path() -> str:
    """Obtiene la ruta de la BD desde secrets o usa valor por defecto."""
    try:
        return st.secrets["paths"]["db_path"]
    except (KeyError, FileNotFoundError):
        # Fallback para desarrollo/testing
        return "./data/sgte.db"


def _get_timeout() -> int:
    """Obtiene el timeout desde secrets o usa valor por defecto."""
    try:
        return st.secrets["database"]["timeout_seconds"]
    except (KeyError, FileNotFoundError):
        return 30


def _get_max_retries() -> int:
    """Obtiene número máximo de reintentos desde secrets."""
    try:
        return st.secrets["database"]["max_retries"]
    except (KeyError, FileNotFoundError):
        return 5


# ============================================
# CONFIGURACIÓN DEL ENGINE
# ============================================

_engine: Engine = None
_SessionLocal: sessionmaker = None


def get_engine() -> Engine:
    """
    Crea y retorna el engine de SQLAlchemy.
    Configurado con:
    - Timeout alto para evitar bloqueos en red
    - check_same_thread=False para uso en Streamlit
    - Pool de conexiones mínimo para SQLite
    """
    global _engine
    
    if _engine is not None:
        return _engine
    
    db_path = _get_db_path()
    timeout = _get_timeout()
    
    # Asegurar que el directorio exista
    db_dir = Path(db_path).parent
    db_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Conectando a base de datos: {db_path}")
    
    _engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={
            "timeout": timeout,
            "check_same_thread": False
        },
        pool_pre_ping=True,  # Verifica conexión antes de usar
        pool_size=1,         # SQLite no soporta múltiples conexiones escritura
        max_overflow=0,      # Sin conexiones adicionales
        echo=False           # Cambiar a True para debug SQL
    )
    
    # Registrar evento para configurar SQLite en cada conexión
    @event.listens_for(_engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        """
        Configura pragmas de SQLite para mejor rendimiento y concurrencia.
        Se ejecuta cada vez que se establece una nueva conexión.
        """
        cursor = dbapi_conn.cursor()
        
        # WAL mode: mejor concurrencia para lectura/escritura
        cursor.execute("PRAGMA journal_mode=WAL")
        
        # Timeout de espera si la BD está bloqueada (en milisegundos)
        cursor.execute(f"PRAGMA busy_timeout={timeout * 1000}")
        
        # Sincronización normal (balance entre seguridad y velocidad)
        cursor.execute("PRAGMA synchronous=NORMAL")
        
        # Cache más grande para mejor rendimiento
        cursor.execute("PRAGMA cache_size=-64000")  # 64MB de cache
        
        # Habilitar foreign keys
        cursor.execute("PRAGMA foreign_keys=ON")
        
        cursor.close()
        logger.debug("SQLite PRAGMAs configurados (WAL mode, foreign keys, cache)")
    
    return _engine


# ============================================
# GESTIÓN DE SESIONES CON RETRY
# ============================================

@retry(
    stop=stop_after_attempt(_get_max_retries()),
    wait=wait_exponential(multiplier=0.5, min=0.5, max=10),
    retry=retry_if_exception_type(sqlite3.OperationalError),
    before_sleep=before_sleep_log(logger, "warning")
)
def get_session() -> Session:
    """
    Obtiene una nueva sesión de base de datos.
    
    Implementa retry automático con backoff exponencial si la BD
    está bloqueada por otro proceso.
    
    Returns:
        Session: Sesión de SQLAlchemy lista para usar.
        
    Raises:
        sqlite3.OperationalError: Si se agotan los reintentos.
        
    Ejemplo:
        session = get_session()
        try:
            # operaciones...
            session.commit()
        finally:
            session.close()
    """
    global _SessionLocal
    
    engine = get_engine()
    
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(
            bind=engine,
            autocommit=False,
            autoflush=False
        )
    
    session = _SessionLocal()
    
    # Test de conexión para activar retry si está bloqueada
    try:
        session.execute(text("SELECT 1"))
    except sqlite3.OperationalError as e:
        session.close()
        logger.warning(f"BD bloqueada, reintentando... ({e})")
        raise
    
    return session


@contextmanager
def get_session_context() -> Generator[Session, None, None]:
    """
    Context manager para sesiones de base de datos.
    Maneja automáticamente commit/rollback y cierre.
    
    Ejemplo:
        with get_session_context() as session:
            estudiante = Estudiante(run="12345678-9", ...)
            session.add(estudiante)
            # commit automático al salir del context
    """
    session = get_session()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Error en transacción, rollback ejecutado: {e}")
        raise
    finally:
        session.close()


# ============================================
# INICIALIZACIÓN DE BASE DE DATOS
# ============================================

def init_database() -> bool:
    """
    Inicializa la base de datos creando todas las tablas.
    
    Returns:
        bool: True si la inicialización fue exitosa.
        
    Notas:
        - Solo crea tablas que no existen (no destruye datos).
        - Configura automáticamente WAL mode.
    """
    try:
        engine = get_engine()
        
        # Crear todas las tablas definidas en models.py
        Base.metadata.create_all(bind=engine)
        
        logger.info("Base de datos inicializada correctamente")
        return True
        
    except Exception as e:
        logger.error(f"Error inicializando base de datos: {e}")
        return False


def check_database_health() -> dict:
    """
    Verifica el estado de salud de la base de datos.
    
    Returns:
        dict: Información sobre el estado de la BD.
    """
    result = {
        "status": "unknown",
        "path": _get_db_path(),
        "wal_mode": False,
        "tables": [],
        "error": None
    }
    
    try:
        with get_session_context() as session:
            # Verificar WAL mode
            wal_result = session.execute(text("PRAGMA journal_mode")).scalar()
            result["wal_mode"] = wal_result == "wal"
            
            # Listar tablas
            tables = session.execute(
                text("SELECT name FROM sqlite_master WHERE type='table'")
            ).fetchall()
            result["tables"] = [t[0] for t in tables]
            
            result["status"] = "healthy"
            
    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)
        logger.error(f"Error verificando salud de BD: {e}")
    
    return result


# ============================================
# LOGGING A BASE DE DATOS
# ============================================

def log_app_error(
    level: str,
    message: str,
    module: str = None,
    function: str = None,
    traceback: str = None,
    extra_data: str = None
) -> bool:
    """
    Registra un error técnico en la tabla app_logs.
    
    Si la BD no está disponible, hace fallback a log local (loguru).
    
    Args:
        level: Nivel del log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        message: Mensaje descriptivo del error
        module: Módulo que generó el error
        function: Función específica
        traceback: Traceback completo si aplica
        extra_data: Datos adicionales en formato JSON
        
    Returns:
        bool: True si el log se guardó correctamente.
    """
    try:
        from .models import AppLog
        
        with get_session_context() as session:
            log_entry = AppLog(
                level=level.upper(),
                message=message,
                module=module,
                function=function,
                traceback=traceback,
                extra_data=extra_data
            )
            session.add(log_entry)
        
        return True
        
    except Exception as e:
        # Fallback a log local si BD no disponible
        logger.error(f"[LOCAL FALLBACK] {level}: {message} | Error BD: {e}")
        return False


def log_user_action(
    tabla: str,
    registro_id: str,
    accion: str,
    usuario: str = None,
    descripcion: str = None,
    valores_anteriores: str = None,
    valores_nuevos: str = None
) -> bool:
    """
    Registra una acción de usuario en la bitácora.
    
    Args:
        tabla: Nombre de la tabla afectada
        registro_id: ID del registro afectado
        accion: Tipo de acción (CREATE, UPDATE, DELETE, etc.)
        usuario: Nombre del usuario que realizó la acción
        descripcion: Descripción detallada
        valores_anteriores: JSON con valores antes del cambio
        valores_nuevos: JSON con valores después del cambio
        
    Returns:
        bool: True si el log se guardó correctamente.
    """
    try:
        from .models import Bitacora
        
        with get_session_context() as session:
            entry = Bitacora(
                tabla=tabla,
                registro_id=str(registro_id),
                accion=accion,
                usuario=usuario,
                descripcion=descripcion,
                valores_anteriores=valores_anteriores,
                valores_nuevos=valores_nuevos
            )
            session.add(entry)
        
        logger.info(f"Bitácora: {accion} en {tabla}[{registro_id}]")
        return True
        
    except Exception as e:
        logger.error(f"Error registrando en bitácora: {e}")
        return False
