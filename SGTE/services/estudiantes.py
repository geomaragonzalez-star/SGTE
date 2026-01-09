# services/estudiantes.py
"""
Servicio CRUD para gestión de estudiantes (RF-01).
Implementa todas las operaciones de base de datos para la entidad Estudiante.
"""

import re
import json
from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy import or_, func
from loguru import logger

from database import get_session_context, Estudiante, Bitacora
from database.connection import log_user_action


def validar_run(run: str) -> tuple[bool, str]:
    """
    Valida formato y dígito verificador de RUN chileno.
    
    Args:
        run: RUN en formato XX.XXX.XXX-X o XXXXXXXX-X
        
    Returns:
        tuple: (es_valido, mensaje)
    """
    # Limpiar RUN
    run_limpio = run.upper().replace(".", "").replace("-", "").strip()
    
    if len(run_limpio) < 8 or len(run_limpio) > 9:
        return False, "RUN debe tener entre 8 y 9 caracteres"
    
    # Separar número y dígito verificador
    cuerpo = run_limpio[:-1]
    dv_ingresado = run_limpio[-1]
    
    if not cuerpo.isdigit():
        return False, "El cuerpo del RUN debe ser numérico"
    
    # Calcular dígito verificador
    suma = 0
    multiplo = 2
    for c in reversed(cuerpo):
        suma += int(c) * multiplo
        multiplo = multiplo + 1 if multiplo < 7 else 2
    
    resto = suma % 11
    dv_calculado = str(11 - resto) if resto > 1 else ("0" if resto == 0 else "K")
    
    if dv_ingresado != dv_calculado:
        return False, f"Dígito verificador incorrecto. Debería ser {dv_calculado}"
    
    return True, "RUN válido"


def formatear_run(run: str) -> str:
    """Formatea RUN a formato estándar XX.XXX.XXX-X."""
    run_limpio = run.upper().replace(".", "").replace("-", "").strip()
    cuerpo = run_limpio[:-1]
    dv = run_limpio[-1]
    
    # Agregar puntos
    cuerpo_formateado = ""
    for i, c in enumerate(reversed(cuerpo)):
        if i > 0 and i % 3 == 0:
            cuerpo_formateado = "." + cuerpo_formateado
        cuerpo_formateado = c + cuerpo_formateado
    
    return f"{cuerpo_formateado}-{dv}"


def crear_estudiante(
    run: str,
    nombres: str,
    apellidos: str,
    carrera: str,
    modalidad: str,
    usuario: str = None
) -> tuple[bool, str, Optional[Estudiante]]:
    """
    Crea un nuevo estudiante en la base de datos.
    
    Returns:
        tuple: (exito, mensaje, estudiante)
    """
    # Validar RUN
    valido, msg = validar_run(run)
    if not valido:
        return False, msg, None
    
    run_formateado = formatear_run(run)
    
    try:
        with get_session_context() as session:
            # Verificar si ya existe
            existente = session.query(Estudiante).filter(
                Estudiante.run == run_formateado
            ).first()
            
            if existente:
                return False, f"Ya existe un estudiante con RUN {run_formateado}", None
            
            # Crear estudiante
            estudiante = Estudiante(
                run=run_formateado,
                nombres=nombres.strip().title(),
                apellidos=apellidos.strip().title(),
                carrera=carrera.strip(),
                modalidad=modalidad.strip()
            )
            
            session.add(estudiante)
            session.flush()  # Para obtener el objeto con datos
            
            # Registrar en bitácora
            log_user_action(
                tabla="estudiantes",
                registro_id=run_formateado,
                accion="CREATE",
                usuario=usuario,
                descripcion=f"Estudiante creado: {nombres} {apellidos}",
                valores_nuevos=json.dumps({
                    "run": run_formateado,
                    "nombres": nombres,
                    "apellidos": apellidos,
                    "carrera": carrera,
                    "modalidad": modalidad
                })
            )
            
            logger.info(f"Estudiante creado: {run_formateado}")
            return True, "Estudiante creado exitosamente", estudiante
            
    except Exception as e:
        logger.error(f"Error creando estudiante: {e}")
        return False, f"Error de base de datos: {str(e)}", None


def obtener_estudiante(run: str) -> Optional[Estudiante]:
    """Obtiene un estudiante por su RUN."""
    run_formateado = formatear_run(run)
    
    try:
        with get_session_context() as session:
            estudiante = session.query(Estudiante).filter(
                Estudiante.run == run_formateado
            ).first()
            
            if estudiante:
                session.expunge(estudiante)
            return estudiante
            
    except Exception as e:
        logger.error(f"Error obteniendo estudiante: {e}")
        return None


def buscar_estudiantes(
    termino: str = None,
    carrera: str = None,
    limite: int = 100
) -> List[Dict[str, Any]]:
    """
    Busca estudiantes por término (RUN o nombre) y/o carrera.
    
    Returns:
        Lista de diccionarios con datos de estudiantes.
    """
    try:
        with get_session_context() as session:
            query = session.query(Estudiante)
            
            if termino:
                termino_like = f"%{termino}%"
                query = query.filter(
                    or_(
                        Estudiante.run.ilike(termino_like),
                        Estudiante.nombres.ilike(termino_like),
                        Estudiante.apellidos.ilike(termino_like)
                    )
                )
            
            if carrera and carrera != "Todas":
                query = query.filter(Estudiante.carrera == carrera)
            
            estudiantes = query.order_by(Estudiante.apellidos).limit(limite).all()
            
            return [
                {
                    "run": e.run,
                    "nombres": e.nombres,
                    "apellidos": e.apellidos,
                    "nombre_completo": e.nombre_completo,
                    "carrera": e.carrera,
                    "modalidad": e.modalidad,
                    "created_at": e.created_at.isoformat() if e.created_at else None
                }
                for e in estudiantes
            ]
            
    except Exception as e:
        logger.error(f"Error buscando estudiantes: {e}")
        return []


def listar_estudiantes(limite: int = 500) -> List[Dict[str, Any]]:
    """Lista todos los estudiantes."""
    return buscar_estudiantes(limite=limite)


def actualizar_estudiante(
    run: str,
    datos: Dict[str, Any],
    usuario: str = None
) -> tuple[bool, str]:
    """
    Actualiza datos de un estudiante.
    
    Args:
        run: RUN del estudiante
        datos: Diccionario con campos a actualizar
        usuario: Usuario que realiza la acción
    """
    run_formateado = formatear_run(run)
    
    try:
        with get_session_context() as session:
            estudiante = session.query(Estudiante).filter(
                Estudiante.run == run_formateado
            ).first()
            
            if not estudiante:
                return False, f"Estudiante {run_formateado} no encontrado"
            
            # Guardar valores anteriores
            valores_ant = {
                "nombres": estudiante.nombres,
                "apellidos": estudiante.apellidos,
                "carrera": estudiante.carrera,
                "modalidad": estudiante.modalidad
            }
            
            # Actualizar campos permitidos
            if "nombres" in datos:
                estudiante.nombres = datos["nombres"].strip().title()
            if "apellidos" in datos:
                estudiante.apellidos = datos["apellidos"].strip().title()
            if "carrera" in datos:
                estudiante.carrera = datos["carrera"].strip()
            if "modalidad" in datos:
                estudiante.modalidad = datos["modalidad"].strip()
            
            estudiante.updated_at = datetime.now()
            
            # Bitácora
            log_user_action(
                tabla="estudiantes",
                registro_id=run_formateado,
                accion="UPDATE",
                usuario=usuario,
                descripcion="Datos de estudiante actualizados",
                valores_anteriores=json.dumps(valores_ant),
                valores_nuevos=json.dumps(datos)
            )
            
            logger.info(f"Estudiante actualizado: {run_formateado}")
            return True, "Estudiante actualizado exitosamente"
            
    except Exception as e:
        logger.error(f"Error actualizando estudiante: {e}")
        return False, f"Error: {str(e)}"


def eliminar_estudiante(run: str, usuario: str = None) -> tuple[bool, str]:
    """Elimina un estudiante (soft delete o hard delete)."""
    run_formateado = formatear_run(run)
    
    try:
        with get_session_context() as session:
            estudiante = session.query(Estudiante).filter(
                Estudiante.run == run_formateado
            ).first()
            
            if not estudiante:
                return False, f"Estudiante {run_formateado} no encontrado"
            
            nombre = estudiante.nombre_completo
            session.delete(estudiante)
            
            log_user_action(
                tabla="estudiantes",
                registro_id=run_formateado,
                accion="DELETE",
                usuario=usuario,
                descripcion=f"Estudiante eliminado: {nombre}"
            )
            
            logger.warning(f"Estudiante eliminado: {run_formateado}")
            return True, f"Estudiante {nombre} eliminado"
            
    except Exception as e:
        logger.error(f"Error eliminando estudiante: {e}")
        return False, f"Error: {str(e)}"


def obtener_carreras() -> List[str]:
    """Obtiene lista única de carreras registradas."""
    try:
        with get_session_context() as session:
            carreras = session.query(Estudiante.carrera).distinct().all()
            return sorted([c[0] for c in carreras if c[0]])
    except Exception as e:
        logger.error(f"Error obteniendo carreras: {e}")
        return []


def contar_estudiantes() -> int:
    """Cuenta total de estudiantes."""
    try:
        with get_session_context() as session:
            return session.query(func.count(Estudiante.run)).scalar() or 0
    except Exception as e:
        logger.error(f"Error contando estudiantes: {e}")
        return 0


def contar_estudiantes_por_estado() -> Dict[str, int]:
    """
    Cuenta estudiantes agrupados por estado de expediente.
    
    Returns:
        Diccionario con conteos por estado: {
            'pendientes': int,
            'en_proceso': int,
            'listos': int,
            'titulados': int
        }
    """
    try:
        from database.models import Proyecto, Expediente, EstadoExpediente
        
        with get_session_context() as session:
            # Contar por cada estado
            result = {
                'pendientes': 0,
                'en_proceso': 0,
                'listos': 0,
                'titulados': 0
            }
            
            # Contar pendientes (PENDIENTE)
            result['pendientes'] = session.query(func.count(func.distinct(Proyecto.estudiante_run1)))\
                .join(Expediente, Proyecto.id == Expediente.proyecto_id)\
                .filter(Expediente.estado == EstadoExpediente.PENDIENTE)\
                .scalar() or 0
            
            # Contar en proceso (EN_PROCESO, LISTO_ENVIO, ENVIADO)
            result['en_proceso'] = session.query(func.count(func.distinct(Proyecto.estudiante_run1)))\
                .join(Expediente, Proyecto.id == Expediente.proyecto_id)\
                .filter(Expediente.estado.in_([
                    EstadoExpediente.EN_PROCESO,
                    EstadoExpediente.LISTO_ENVIO,
                    EstadoExpediente.ENVIADO
                ]))\
                .scalar() or 0
            
            # Contar listos (APROBADO)
            result['listos'] = session.query(func.count(func.distinct(Proyecto.estudiante_run1)))\
                .join(Expediente, Proyecto.id == Expediente.proyecto_id)\
                .filter(Expediente.estado == EstadoExpediente.APROBADO)\
                .scalar() or 0
            
            # Contar titulados (TITULADO)
            result['titulados'] = session.query(func.count(func.distinct(Proyecto.estudiante_run1)))\
                .join(Expediente, Proyecto.id == Expediente.proyecto_id)\
                .filter(Expediente.estado == EstadoExpediente.TITULADO)\
                .scalar() or 0
            
            return result
            
    except Exception as e:
        logger.error(f"Error contando estudiantes por estado: {e}")
        return {
            'pendientes': 0,
            'en_proceso': 0,
            'listos': 0,
            'titulados': 0
        }
