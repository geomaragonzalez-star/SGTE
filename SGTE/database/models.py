# database/models.py
"""
Modelos SQLAlchemy para SGTE.
Definición de todas las tablas del sistema.
"""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    String, 
    Integer, 
    Boolean, 
    DateTime, 
    Text, 
    ForeignKey,
    Enum as SQLEnum
)
from sqlalchemy.orm import (
    DeclarativeBase, 
    Mapped, 
    mapped_column, 
    relationship
)
import enum


class Base(DeclarativeBase):
    """Clase base para todos los modelos."""
    pass


# ============================================
# ENUMS
# ============================================

class EstadoExpediente(enum.Enum):
    """Estados posibles del expediente (semáforo)."""
    PENDIENTE = "pendiente"           # 🔴 Rojo
    EN_PROCESO = "en_proceso"         # 🟡 Amarillo
    LISTO_ENVIO = "listo_envio"       # 🟢 Verde
    ENVIADO = "enviado"               # 📤 Enviado a Registro
    APROBADO = "aprobado"             # ✅ Aprobado por Registro
    TITULADO = "titulado"             # 🎓 Titulado


class ModalidadProyecto(enum.Enum):
    """Modalidades de titulación."""
    TESIS = "tesis"
    PROYECTO = "proyecto"
    SEMINARIO = "seminario"
    PRACTICA = "practica_profesional"
    EXAMEN = "examen_titulo"


class TipoDocumento(enum.Enum):
    """Tipos de documentos habilitantes."""
    BIENESTAR = "bienestar"
    FINANZAS_TITULO = "finanzas_titulo"
    FINANZAS_LICENCIA = "finanzas_licencia"
    BIBLIOTECA = "biblioteca"
    SDT = "sdt"
    MEMORANDUM = "memorandum"
    ACTA = "acta"
    OTRO = "otro"


class TipoHito(enum.Enum):
    """Tipos de hitos del proceso de titulación."""
    NOTIFICACION_COMISION = "notificacion_comision"
    ENTREGA_AVANCE = "entrega_avance"
    PRESENTACION_AVANCE = "presentacion_avance"
    ENTREGA_DOC_FINAL = "entrega_doc_final"
    ACEPTACION_BIBLIOTECA = "aceptacion_biblioteca"
    EXAMEN_GRADO = "examen_grado"


class NivelLog(enum.Enum):
    """Niveles de log para AppLog."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


# ============================================
# MODELOS PRINCIPALES
# ============================================

class Estudiante(Base):
    """
    Tabla de estudiantes.
    RUN es la clave primaria (identificador único chileno).
    """
    __tablename__ = "estudiantes"
    
    # Clave primaria
    run: Mapped[str] = mapped_column(String(12), primary_key=True)
    
    # Datos personales
    nombres: Mapped[str] = mapped_column(String(100), nullable=False)
    apellidos: Mapped[str] = mapped_column(String(100), nullable=False)
    carrera: Mapped[str] = mapped_column(String(150), nullable=False)
    modalidad: Mapped[str] = mapped_column(String(20), nullable=False)
    
    # Auditoría
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, onupdate=datetime.now
    )
    
    # Relaciones
    proyectos_1: Mapped[List["Proyecto"]] = relationship(
        back_populates="estudiante_1", foreign_keys="[Proyecto.estudiante_run1]", cascade="all, delete-orphan"
    )
    proyectos_2: Mapped[List["Proyecto"]] = relationship(
        back_populates="estudiante_2", foreign_keys="[Proyecto.estudiante_run2]", cascade="all, delete-orphan"
    )
    documentos: Mapped[List["Documento"]] = relationship(
        back_populates="estudiante", cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<Estudiante(run='{self.run}', nombre='{self.nombres} {self.apellidos}')>"
    
    @property
    def nombre_completo(self) -> str:
        """Retorna nombre completo del estudiante."""
        return f"{self.nombres} {self.apellidos}"


class Proyecto(Base):
    """
    Tabla de proyectos de titulación.
    Un estudiante puede tener múltiples proyectos (ej: reprobó y volvió a inscribir).
    """
    __tablename__ = "proyectos"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # FK a estudiantes
    estudiante_run1: Mapped[str] = mapped_column(
        String(12), ForeignKey("estudiantes.run"), nullable=False
    )
    estudiante_run2: Mapped[Optional[str]] = mapped_column(
        String(12), ForeignKey("estudiantes.run")
    )
    
    # Datos del proyecto
    semestre: Mapped[str] = mapped_column(String(10), nullable=False)  # Ej: "2026-1"
    modalidad_titulacion: Mapped[str] = mapped_column(
        String(50), nullable=False
    )
    titulo: Mapped[Optional[str]] = mapped_column(String(500))
    link_documento: Mapped[Optional[str]] = mapped_column(String(500))
    
    # Auditoría
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, onupdate=datetime.now
    )
    
    # Relaciones
    estudiante_1: Mapped["Estudiante"] = relationship(foreign_keys=[estudiante_run1], back_populates="proyectos_1")
    estudiante_2: Mapped[Optional["Estudiante"]] = relationship(foreign_keys=[estudiante_run2], back_populates="proyectos_2")
    comision: Mapped[Optional["Comision"]] = relationship(
        back_populates="proyecto", uselist=False, cascade="all, delete-orphan"
    )
    expediente: Mapped[Optional["Expediente"]] = relationship(
        back_populates="proyecto", uselist=False, cascade="all, delete-orphan"
    )
    hitos: Mapped[List["Hito"]] = relationship(
        back_populates="proyecto", cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<Proyecto(id={self.id}, estudiante='{self.estudiante_run}', semestre='{self.semestre}')>"


class Comision(Base):
    """
    Tabla de comisiones evaluadoras.
    Cada proyecto tiene una comisión asignada.
    """
    __tablename__ = "comisiones"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # FK a proyecto
    proyecto_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("proyectos.id"), nullable=False, unique=True
    )
    
    # Miembros de la comisión
    profesor_guia: Mapped[Optional[str]] = mapped_column(String(150))
    corrector_1: Mapped[Optional[str]] = mapped_column(String(150))
    corrector_2: Mapped[Optional[str]] = mapped_column(String(150))
    
    # Relación
    proyecto: Mapped["Proyecto"] = relationship(back_populates="comision")
    
    def __repr__(self) -> str:
        return f"<Comision(proyecto_id={self.proyecto_id}, guia='{self.profesor_guia}')>"


class Expediente(Base):
    """
    Tabla de estado del expediente.
    Controla el flujo de aprobación y envío a Registro Curricular.
    """
    __tablename__ = "expedientes"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # FK a proyecto
    proyecto_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("proyectos.id"), nullable=False, unique=True
    )
    
    # Estado del expediente (semáforo)
    estado: Mapped[EstadoExpediente] = mapped_column(
        SQLEnum(EstadoExpediente), 
        default=EstadoExpediente.PENDIENTE,
        nullable=False
    )
    
    # Observaciones y notas
    observaciones: Mapped[Optional[str]] = mapped_column(Text)
    
    # Fechas de control
    fecha_envio: Mapped[Optional[datetime]] = mapped_column(DateTime)
    fecha_aprobacion: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    # Cierre
    titulado: Mapped[bool] = mapped_column(Boolean, default=False)
    semestre_titulacion: Mapped[Optional[str]] = mapped_column(String(10))
    
    # Auditoría
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, onupdate=datetime.now
    )
    
    # Relación
    proyecto: Mapped["Proyecto"] = relationship(back_populates="expediente")
    
    def __repr__(self) -> str:
        return f"<Expediente(proyecto_id={self.proyecto_id}, estado='{self.estado.value}')>"


class Hito(Base):
    """
    Tabla de hitos del proceso de titulación.
    Registra fechas clave como entregas, presentaciones, etc.
    """
    __tablename__ = "hitos"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # FK a proyecto
    proyecto_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("proyectos.id"), nullable=False
    )
    
    # Tipo de hito
    tipo: Mapped[TipoHito] = mapped_column(SQLEnum(TipoHito), nullable=False)
    
    # Fecha del hito
    fecha: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    # Estado
    completado: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Notas adicionales
    observaciones: Mapped[Optional[str]] = mapped_column(Text)
    
    # Relación
    proyecto: Mapped["Proyecto"] = relationship(back_populates="hitos")
    
    def __repr__(self) -> str:
        return f"<Hito(tipo='{self.tipo.value}', completado={self.completado})>"


class Documento(Base):
    """
    Tabla de documentos habilitantes.
    Controla el checklist de documentos requeridos por estudiante.
    """
    __tablename__ = "documentos"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # FK a estudiante
    estudiante_run: Mapped[str] = mapped_column(
        String(12), ForeignKey("estudiantes.run"), nullable=False
    )
    
    # Tipo de documento
    tipo: Mapped[TipoDocumento] = mapped_column(SQLEnum(TipoDocumento), nullable=False)
    
    # Ruta al archivo
    path: Mapped[Optional[str]] = mapped_column(String(500))
    
    # Estado de validación
    validado: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Auditoría
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    validated_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    validated_by: Mapped[Optional[str]] = mapped_column(String(100))
    
    # Relación
    estudiante: Mapped["Estudiante"] = relationship(back_populates="documentos")
    
    def __repr__(self) -> str:
        return f"<Documento(tipo='{self.tipo.value}', validado={self.validado})>"


# ============================================
# MODELOS DE AUDITORÍA Y LOGS
# ============================================

class Bitacora(Base):
    """
    Tabla de bitácora de acciones de usuario.
    Registra todas las operaciones CRUD para auditoría.
    """
    __tablename__ = "bitacora"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Qué tabla fue afectada
    tabla: Mapped[str] = mapped_column(String(50), nullable=False)
    
    # ID del registro afectado
    registro_id: Mapped[str] = mapped_column(String(50), nullable=False)
    
    # Acción realizada (CREATE, UPDATE, DELETE, etc.)
    accion: Mapped[str] = mapped_column(String(50), nullable=False)
    
    # Usuario que realizó la acción
    usuario: Mapped[Optional[str]] = mapped_column(String(100))
    
    # Descripción detallada del cambio
    descripcion: Mapped[Optional[str]] = mapped_column(Text)
    
    # Valores antiguos y nuevos (JSON serializado)
    valores_anteriores: Mapped[Optional[str]] = mapped_column(Text)
    valores_nuevos: Mapped[Optional[str]] = mapped_column(Text)
    
    # Timestamp
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    
    def __repr__(self) -> str:
        return f"<Bitacora(tabla='{self.tabla}', accion='{self.accion}', timestamp='{self.timestamp}')>"


class AppLog(Base):
    """
    Tabla de logs técnicos del sistema.
    Registra errores y eventos para debugging.
    """
    __tablename__ = "app_logs"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Nivel de log
    level: Mapped[str] = mapped_column(String(20), nullable=False)
    
    # Mensaje del log
    message: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Módulo que generó el log
    module: Mapped[Optional[str]] = mapped_column(String(100))
    
    # Función específica
    function: Mapped[Optional[str]] = mapped_column(String(100))
    
    # Traceback completo si es error
    traceback: Mapped[Optional[str]] = mapped_column(Text)
    
    # Datos adicionales (JSON)
    extra_data: Mapped[Optional[str]] = mapped_column(Text)
    
    # Timestamp
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    
    def __repr__(self) -> str:
        return f"<AppLog(level='{self.level}', message='{self.message[:50]}...')>"
