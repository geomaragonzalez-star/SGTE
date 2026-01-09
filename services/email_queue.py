# services/email_queue.py
"""
Cola de Correos Outlook (RF-05, HU-04).
Automatización de envío de solicitudes a Registro Curricular.
"""

import time
from pathlib import Path
from typing import List, Dict, Optional, Callable
from datetime import datetime
from dataclasses import dataclass, field
from loguru import logger

# Windows COM para Outlook
try:
    import win32com.client
    import pythoncom
    HAS_OUTLOOK = True
except ImportError:
    HAS_OUTLOOK = False
    logger.warning("pywin32 no instalado. Funcionalidad Outlook deshabilitada.")

from config import get_config
from database import get_session_context, Estudiante, Documento, Expediente, EstadoExpediente
from database.connection import log_user_action


# ============================================
# EXCEPCIONES PERSONALIZADAS
# ============================================

class OutlookNotInstalledException(Exception):
    """Outlook no está instalado en este equipo."""
    pass


class OutlookBusyException(Exception):
    """Outlook está bloqueado por un diálogo modal."""
    pass


class OutlookConnectionError(Exception):
    """Error de conexión con Outlook."""
    pass


# ============================================
# DATACLASSES
# ============================================

@dataclass
class DatosCorreo:
    """Datos para un correo individual."""
    run: str
    nombre: str
    email_estudiante: Optional[str]
    carrera: str
    adjuntos: List[Path] = field(default_factory=list)


@dataclass
class ResultadoEnvio:
    """Resultado del envío de un correo."""
    run: str
    exito: bool
    mensaje: str
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ResultadoEnvioMasivo:
    """Resultado del envío masivo de correos."""
    total: int
    exitosos: int
    fallidos: int
    resultados: List[ResultadoEnvio]
    tiempo_total: float
    interrumpido: bool = False


# ============================================
# CLASE PRINCIPAL
# ============================================

class OutlookMailer:
    """Gestor de envío de correos vía Outlook."""
    
    def __init__(self):
        self.outlook = None
        self.config = get_config()
        self.delay = self.config.email.send_delay_seconds
        self.destinatario = self.config.email.registro_curricular
    
    def _init_outlook(self) -> bool:
        """
        Inicializa conexión con Outlook.
        
        Returns:
            bool: True si la conexión fue exitosa
            
        Raises:
            OutlookNotInstalledException: Si Outlook no está instalado
            OutlookBusyException: Si Outlook está bloqueado
        """
        if not HAS_OUTLOOK:
            raise OutlookNotInstalledException(
                "pywin32 no está instalado. Ejecute: pip install pywin32"
            )
        
        try:
            # Inicializar COM en el thread actual
            pythoncom.CoInitialize()
            
            # Obtener instancia de Outlook
            self.outlook = win32com.client.Dispatch("Outlook.Application")
            
            # Verificar que Outlook responde
            namespace = self.outlook.GetNamespace("MAPI")
            _ = namespace.CurrentUser
            
            logger.info("Conexión con Outlook establecida")
            return True
            
        except pythoncom.com_error as e:
            error_code = getattr(e, 'hresult', None)
            
            if error_code == -2147221005:  # CO_E_CLASSSTRING
                raise OutlookNotInstalledException(
                    "Microsoft Outlook no está instalado en este equipo."
                )
            elif error_code == -2147417848:  # RPC_E_CANTCALLOUT_ININPUTSYNCCALL
                raise OutlookBusyException(
                    "Outlook está mostrando un diálogo. Cierre todos los diálogos y reintente."
                )
            else:
                logger.error(f"Error COM: {e}")
                raise OutlookConnectionError(f"Error conectando a Outlook: {e}")
                
        except Exception as e:
            logger.error(f"Error inesperado conectando a Outlook: {e}")
            raise OutlookConnectionError(str(e))
    
    def _cleanup(self):
        """Limpia recursos COM."""
        try:
            if HAS_OUTLOOK:
                pythoncom.CoUninitialize()
        except:
            pass
        self.outlook = None
    
    def _get_adjuntos(self, run: str) -> List[Path]:
        """Obtiene lista de documentos adjuntos para un estudiante."""
        adjuntos = []
        
        try:
            with get_session_context() as session:
                documentos = session.query(Documento).filter(
                    Documento.estudiante_run == run,
                    Documento.validado == True
                ).all()
                
                for doc in documentos:
                    if doc.path:
                        ruta = Path(doc.path)
                        if ruta.exists():
                            adjuntos.append(ruta)
                        else:
                            logger.warning(f"Documento no encontrado: {ruta}")
        
        except Exception as e:
            logger.error(f"Error obteniendo adjuntos: {e}")
        
        return adjuntos
    
    def _build_subject(self, datos: DatosCorreo) -> str:
        """Construye el asunto del correo."""
        return f"Solicitud Apertura Expediente - {datos.run} - {datos.nombre}"
    
    def _build_body(self, datos: DatosCorreo) -> str:
        """Construye el cuerpo del correo."""
        return f"""Estimados,

Por medio del presente, se remite la solicitud de apertura de expediente de titulación para:

Estudiante: {datos.nombre}
RUN: {datos.run}
Carrera: {datos.carrera}
Email Estudiante: {datos.email_estudiante or 'No registrado'}

Se adjuntan los documentos habilitantes correspondientes.

Atentamente,
Secretaría Docente
Facultad de Ingeniería
Universidad de Santiago de Chile

---
Este correo fue generado automáticamente por SGTE v{self.config.app.version}
Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}
"""
    
    def _actualizar_estado_expediente(self, run: str):
        """Actualiza el estado del expediente a 'Enviado'."""
        try:
            with get_session_context() as session:
                # Buscar proyecto del estudiante
                from database import Proyecto
                proyecto = session.query(Proyecto).filter(
                    Proyecto.estudiante_run == run
                ).order_by(Proyecto.created_at.desc()).first()
                
                if proyecto:
                    expediente = session.query(Expediente).filter(
                        Expediente.proyecto_id == proyecto.id
                    ).first()
                    
                    if expediente:
                        expediente.estado = EstadoExpediente.ENVIADO
                        expediente.fecha_envio = datetime.now()
                    
                    log_user_action(
                        tabla="expedientes",
                        registro_id=str(proyecto.id),
                        accion="UPDATE",
                        descripcion=f"Expediente enviado a Registro Curricular"
                    )
                        
        except Exception as e:
            logger.error(f"Error actualizando expediente: {e}")
    
    def enviar_correo(
        self,
        datos: DatosCorreo,
        solo_borrador: bool = False
    ) -> ResultadoEnvio:
        """
        Envía un correo individual.
        
        Args:
            datos: Datos del correo a enviar
            solo_borrador: Si True, guarda en Drafts sin enviar
            
        Returns:
            ResultadoEnvio
        """
        try:
            if not self.outlook:
                self._init_outlook()
            
            # Crear correo
            mail = self.outlook.CreateItem(0)  # 0 = olMailItem
            mail.To = self.destinatario
            mail.Subject = self._build_subject(datos)
            mail.Body = self._build_body(datos)
            
            # Agregar adjuntos
            for adjunto in datos.adjuntos:
                if adjunto.exists():
                    mail.Attachments.Add(str(adjunto))
                    logger.debug(f"Adjunto agregado: {adjunto.name}")
            
            if solo_borrador:
                mail.Save()
                mensaje = "Correo guardado en borradores"
            else:
                mail.Send()
                mensaje = "Correo enviado exitosamente"
                self._actualizar_estado_expediente(datos.run)
            
            logger.info(f"Correo para {datos.run}: {mensaje}")
            
            return ResultadoEnvio(
                run=datos.run,
                exito=True,
                mensaje=mensaje
            )
            
        except pythoncom.com_error as e:
            if getattr(e, 'hresult', None) == -2147417848:
                raise OutlookBusyException("Outlook requiere atención.")
            
            logger.error(f"Error COM enviando correo: {e}")
            return ResultadoEnvio(
                run=datos.run,
                exito=False,
                mensaje=f"Error COM: {e}"
            )
            
        except Exception as e:
            logger.error(f"Error enviando correo: {e}")
            return ResultadoEnvio(
                run=datos.run,
                exito=False,
                mensaje=str(e)
            )
    
    def enviar_batch(
        self,
        runs: List[str],
        callback: Optional[Callable[[int, int, str], None]] = None,
        solo_borrador: bool = False
    ) -> ResultadoEnvioMasivo:
        """
        Envía correos en lote con delay controlado.
        
        Args:
            runs: Lista de RUNs a procesar
            callback: Función callback(actual, total, run) para progreso
            solo_borrador: Si True, guarda en borradores sin enviar
            
        Returns:
            ResultadoEnvioMasivo
        """
        inicio = datetime.now()
        resultados = []
        exitosos = 0
        fallidos = 0
        interrumpido = False
        
        try:
            self._init_outlook()
            
            for i, run in enumerate(runs):
                if callback:
                    callback(i + 1, len(runs), run)
                
                # Obtener datos del estudiante
                try:
                    with get_session_context() as session:
                        estudiante = session.query(Estudiante).filter(
                            Estudiante.run == run
                        ).first()
                        
                        if not estudiante:
                            resultados.append(ResultadoEnvio(
                                run=run,
                                exito=False,
                                mensaje="Estudiante no encontrado"
                            ))
                            fallidos += 1
                            continue
                        
                        datos = DatosCorreo(
                            run=run,
                            nombre=estudiante.nombre_completo,
                            email_estudiante=estudiante.email,
                            carrera=estudiante.carrera,
                            adjuntos=self._get_adjuntos(run)
                        )
                
                except Exception as e:
                    resultados.append(ResultadoEnvio(
                        run=run,
                        exito=False,
                        mensaje=f"Error obteniendo datos: {e}"
                    ))
                    fallidos += 1
                    continue
                
                # Enviar correo
                resultado = self.enviar_correo(datos, solo_borrador=solo_borrador)
                resultados.append(resultado)
                
                if resultado.exito:
                    exitosos += 1
                else:
                    fallidos += 1
                
                # Delay entre envíos para evitar bloqueo
                if i < len(runs) - 1:
                    time.sleep(self.delay)
                    
        except OutlookBusyException as e:
            logger.warning(f"Proceso interrumpido: {e}")
            interrumpido = True
            resultados.append(ResultadoEnvio(
                run="SISTEMA",
                exito=False,
                mensaje=str(e)
            ))
            
        except Exception as e:
            logger.error(f"Error en batch: {e}")
            interrumpido = True
            
        finally:
            self._cleanup()
        
        tiempo_total = (datetime.now() - inicio).total_seconds()
        
        return ResultadoEnvioMasivo(
            total=len(runs),
            exitosos=exitosos,
            fallidos=fallidos,
            resultados=resultados,
            tiempo_total=tiempo_total,
            interrumpido=interrumpido
        )


# ============================================
# API SIMPLIFICADA
# ============================================

def verificar_outlook() -> tuple[bool, str]:
    """Verifica si Outlook está disponible."""
    if not HAS_OUTLOOK:
        return False, "pywin32 no instalado"
    
    try:
        mailer = OutlookMailer()
        mailer._init_outlook()
        mailer._cleanup()
        return True, "Outlook disponible"
    except OutlookNotInstalledException:
        return False, "Outlook no está instalado"
    except OutlookBusyException:
        return False, "Outlook está bloqueado por un diálogo"
    except Exception as e:
        return False, str(e)


def enviar_correos_masivo(
    runs: List[str],
    callback=None,
    solo_borrador: bool = False
) -> ResultadoEnvioMasivo:
    """
    Función de conveniencia para envío masivo.
    
    Args:
        runs: Lista de RUNs
        callback: Función de progreso
        solo_borrador: Solo guardar borradores
        
    Returns:
        ResultadoEnvioMasivo
    """
    mailer = OutlookMailer()
    return mailer.enviar_batch(runs, callback, solo_borrador)
