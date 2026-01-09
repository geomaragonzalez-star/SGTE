# database/connection.py
"""
Módulo de conexión a base de datos SQLite con patrón de retry.
Diseñado para ser resiliente a bloqueos en entornos de red compartida.

OPTIMIZACIONES v2.1:
- @st.cache_resource en get_engine() para singleton persistente
- PRAGMAs optimizados para latencia de red (mmap_size, temp_store)
- TTL en caché de sesiones para balance entre frescura y velocidad
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
# CONFIGURACIÓN DEL ENGINE (CACHED)
# ============================================

@st.cache_resource(show_spinner="Conectando a base de datos...")
def get_engine() -> Engine:
    """
    Crea y retorna el engine de SQLAlchemy (SINGLETON CACHEADO).
    
    OPTIMIZACIONES:
    - @st.cache_resource: El engine se crea UNA SOLA VEZ por sesión de Streamlit
    - PRAGMAs para red: mmap_size (mapeo en memoria), temp_store (RAM)
    - WAL mode: Permite lecturas concurrentes sin bloqueos
    - Cache de 128MB: Reduce accesos a disco en red
    
    Returns:
        Engine: Motor de SQLAlchemy configurado y optimizado.
    """
    db_path = _get_db_path()
    timeout = _get_timeout()
    
    # Asegurar que el directorio exista
    db_dir = Path(db_path).parent
    db_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"🔌 Creando engine SQLite (CACHED): {db_path}")
    
    engine = create_engine(
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
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        """
        Configura pragmas de SQLite para mejor rendimiento y concurrencia.
        
        OPTIMIZACIONES PARA RED:
        - journal_mode=WAL: Escrituras no bloquean lecturas
        - synchronous=NORMAL: Balance seguridad/velocidad (FULL es muy lento en red)
        - cache_size=-131072: 128MB de cache en RAM (reduce I/O de red)
        - temp_store=MEMORY: Tablas temporales en RAM (no en disco de red)
        - mmap_size=268435456: 256MB de mapeo en memoria (acelera lecturas)
        - page_size=4096: Tamaño óptimo para sistemas modernos
        """
        cursor = dbapi_conn.cursor()
        
        # WAL mode: mejor concurrencia para lectura/escritura
        cursor.execute("PRAGMA journal_mode=WAL")
        
        # Timeout de espera si la BD está bloqueada (en milisegundos)
        cursor.execute(f"PRAGMA busy_timeout={timeout * 1000}")
        
        # Sincronización NORMAL (no FULL) para velocidad en red
        cursor.execute("PRAGMA synchronous=NORMAL")
        
        # Cache de 128MB (negativo = KB, positivo = páginas)
        cursor.execute("PRAGMA cache_size=-131072")
        
        # Tablas temporales en RAM (no en disco de red)
        cursor.execute("PRAGMA temp_store=MEMORY")
        
        # Memory-mapped I/O de 256MB (acelera lecturas grandes)
        cursor.execute("PRAGMA mmap_size=268435456")
        
        # Tamaño de página óptimo (4KB)
        cursor.execute("PRAGMA page_size=4096")
        
        # Habilitar foreign keys
        cursor.execute("PRAGMA foreign_keys=ON")
        
        cursor.close()
        logger.debug("✅ SQLite PRAGMAs optimizados para red aplicados")
    
    return engine


# ============================================
# GESTIÓN DE SESIONES CON RETRY
# ============================================

# SessionLocal factory (se crea una vez)
_SessionLocal: sessionmaker = None


def _get_session_factory() -> sessionmaker:
    """Obtiene o crea el SessionLocal factory (singleton interno)."""
    global _SessionLocal
    
    if _SessionLocal is None:
        engine = get_engine()  # Usa el engine cacheado
        _SessionLocal = sessionmaker(
            bind=engine,
            autocommit=False,
            autoflush=False
        )
        logger.debug("📦 SessionLocal factory creado")
    
    return _SessionLocal


@retry(
    stop=stop_after_attempt(_get_max_retries()),
    wait=wait_exponential(multiplier=0.5, min=0.5, max=10),
    retry=retry_if_exception_type(sqlite3.OperationalError),
    before_sleep=before_sleep_log(logger, "warning")
)
def get_session() -> Session:
    """
    Obtiene una nueva sesión de base de datos.
    
    NOTA: No se cachea con @st.cache_resource porque las sesiones
    deben cerrarse después de cada transacción. El engine SÍ está cacheado.
    
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
    factory = _get_session_factory()
    session = factory()
    
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
        engine = get_engine()  # Usa el engine cacheado
        
        # Crear todas las tablas definidas en models.py
        Base.metadata.create_all(bind=engine)
        
        logger.info("✅ Base de datos inicializada correctamente")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error inicializando base de datos: {e}")
        return False


@st.cache_data(ttl=60, show_spinner=False)
def check_database_health() -> dict:
    """
    Verifica el estado de salud de la base de datos.
    
    OPTIMIZACIÓN: Cacheado por 60 segundos (no necesita verificarse en cada rerun).
    
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
        logger.error(f"❌ Error verificando salud de BD: {e}")
    
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
        
        logger.info(f"📝 Bitácora: {accion} en {tabla}[{registro_id}]")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error registrando en bitácora: {e}")
        return False
