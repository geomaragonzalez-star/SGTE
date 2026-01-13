# services/sync_excel.py
"""
Sincronización Manual desde Excel (ETL).
Importa datos desde archivo Excel histórico de Google Drive a SQLite.
"""

import re
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, Tuple, List
import pandas as pd
from loguru import logger

from database import (
    get_session_context,
    Estudiante,
    Proyecto,
    Comision,
    Expediente,
    EstadoExpediente
)
from database.connection import log_user_action
from services.estudiantes import formatear_run, validar_run


# ============================================
# CONFIGURACIÓN
# ============================================

# Importar configuración centralizada
from config import get_config

def _get_excel_path() -> str:
    """Obtiene la ruta del archivo Excel desde la configuración."""
    try:
        config = get_config()
        return config.excel.ruta_archivo
    except Exception:
        return r"G:\Mi unidad\SGTE\alumnos.xlsx"

def _get_hojas_excel() -> list:
    """Obtiene las hojas del Excel desde la configuración."""
    try:
        config = get_config()
        return config.excel.hojas
    except Exception:
        return [
            "2025-2", "2025-1", "2024-2", "2024-1",
            "Carga Consolidada 2025-2", "Carga Consolidada 2025-1",
            "Carga Consolidada 2024-2", "Carga Consolidada 2024-1"
        ]

# Ruta del archivo Excel en Google Drive (para compatibilidad)
EXCEL_PATH = _get_excel_path()

# Hojas del Excel que deben ser procesadas (para compatibilidad)
HOJAS_EXCEL = _get_hojas_excel()

# Mapeo de columnas del Excel a campos del modelo
# Soporta múltiples formatos de nombres de columna
COLUMN_MAPPING = {
    # Formato snake_case (actual del Excel del usuario)
    "run_1": "run",
    "nombres_1": "nombres",
    "paterno_1": "paterno",
    "materno_1": "materno",
    "carrera_1": "carrera",
    "guia": "profesor_guia",
    "titulo_proyecto": "titulo_proyecto",
    "semestre": "semestre",
    "estado": "estado",
    "modalidad_titulacion": "modalidad",
    # Formato alternativo con mayúsculas (legacy)
    "R.U.N 1": "run",
    "RUN 1": "run",
    "RUN_1": "run",
    "NOMBRES 1": "nombres",
    "NOMBRES_1": "nombres",
    "PATERNO 1": "paterno",
    "PATERNO_1": "paterno",
    "MATERNO 1": "materno",
    "MATERNO_1": "materno",
    "CARRERA": "carrera",
    "CARRERA_1": "carrera",
    "PROFESOR GUÍA": "profesor_guia",
    "PROFESOR_GUIA": "profesor_guia",
    "TÍTULO DEL PROYECTO": "titulo_proyecto",
    "TITULO_PROYECTO": "titulo_proyecto",
    "SEMESTRE": "semestre",
    "ESTADO": "estado"
}

# Valores por defecto
DEFAULT_MODALIDAD_ESTUDIANTE = "Diurno"  # Si no se especifica en Excel
DEFAULT_MODALIDAD_TITULACION = "Trabajo de Titulación"  # Si no se especifica


# ============================================
# FUNCIONES AUXILIARES
# ============================================

def limpiar_run(run_raw: Any) -> Optional[str]:
    """
    Limpia y formatea el RUN desde el Excel.
    Elimina puntos y espacios, mantiene solo números y guion.
    
    Args:
        run_raw: Valor crudo del Excel (puede ser string, float, etc.)
        
    Returns:
        RUN formateado (XX.XXX.XXX-X) o None si no es válido.
    """
    if pd.isna(run_raw) or run_raw == 'nan' or run_raw == '':
        return None
    
    # Convertir a string y limpiar
    run_str = str(run_raw).strip().upper()
    
    # Eliminar puntos y espacios, mantener solo números y guion/K
    run_limpio = re.sub(r'[^\dK\-]', '', run_str)
    
    # Validar formato básico
    if len(run_limpio) < 9 or len(run_limpio) > 12:
        logger.warning(f"RUN con formato inválido: {run_raw}")
        return None
    
    # Formatear usando la función del módulo estudiantes
    try:
        run_formateado = formatear_run(run_limpio)
        
        # Validar RUN (dígito verificador)
        valido, msg = validar_run(run_formateado)
        if not valido:
            logger.warning(f"RUN inválido: {run_formateado} - {msg}")
            return None
            
        return run_formateado
    except Exception as e:
        logger.error(f"Error formateando RUN {run_raw}: {e}")
        return None


def mapear_estado_excel(estado_excel: Any) -> EstadoExpediente:
    """
    Mapea el valor de estado del Excel al enum EstadoExpediente.
    
    Args:
        estado_excel: Valor del estado en el Excel
        
    Returns:
        EstadoExpediente enum correspondiente.
    """
    if pd.isna(estado_excel) or estado_excel == '' or estado_excel == 'nan':
        return EstadoExpediente.PENDIENTE
    
    estado_str = str(estado_excel).strip().upper()
    
    # Mapeo flexible de estados comunes
    mapeo_estados = {
        'PENDIENTE': EstadoExpediente.PENDIENTE,
        'EN PROCESO': EstadoExpediente.EN_PROCESO,
        'LISTO ENVIO': EstadoExpediente.LISTO_ENVIO,
        'LISTO ENVÍO': EstadoExpediente.LISTO_ENVIO,
        'ENVIADO': EstadoExpediente.ENVIADO,
        'APROBADO': EstadoExpediente.APROBADO,
        'TITULADO': EstadoExpediente.TITULADO
    }
    
    # Buscar coincidencia exacta o parcial
    for clave, estado_enum in mapeo_estados.items():
        if clave in estado_str:
            return estado_enum
    
    # Por defecto, pendiente
    logger.warning(f"Estado no reconocido '{estado_excel}', usando PENDIENTE")
    return EstadoExpediente.PENDIENTE


def normalizar_columna(col_name) -> str:
    """
    Normaliza nombres de columnas para hacer búsqueda flexible.
    Elimina espacios extra, convierte a mayúsculas, etc.
    Maneja columnas con nombres de tipo datetime/int/etc.
    """
    # Convertir a string de forma segura (puede ser datetime, int, etc.)
    col_str = str(col_name) if col_name is not None else ''
    return col_str.strip().upper().replace(' ', ' ')


# ============================================
# LÓGICA DE SINCRONIZACIÓN (ETL)
# ============================================

def leer_excel(ruta: str, hojas: List[str] = None) -> Optional[Dict[str, pd.DataFrame]]:
    """
    Lee el archivo Excel detectando automáticamente la fila de encabezados.
    Busca la fila que contiene 'R.U.N' o 'RUN' como indicador de encabezados.
    
    Args:
        ruta: Ruta al archivo Excel
        hojas: Lista de nombres de hojas a leer. Si es None, usa HOJAS_EXCEL.
        
    Returns:
        Diccionario {nombre_hoja: DataFrame} o None si hay error.
    """
    if hojas is None:
        hojas = HOJAS_EXCEL
    
    try:
        if not Path(ruta).exists():
            logger.error(f"Archivo Excel no encontrado: {ruta}")
            return None
        
        logger.info(f"Leyendo hojas del Excel: {hojas}")
        
        dfs_validos = {}
        
        for nombre_hoja in hojas:
            try:
                # Primero, leer las primeras filas sin encabezado para detectar dónde está
                df_preview = pd.read_excel(
                    ruta, 
                    sheet_name=nombre_hoja, 
                    header=None,  # Sin encabezado, leer todo como datos
                    nrows=5,  # Solo primeras 5 filas para encontrar encabezados
                    engine='openpyxl'
                )
                
                # Buscar la fila que contiene "R.U.N", "RUN" o "run_1" (puede ser en cualquier columna)
                header_row = None
                for idx, row in df_preview.iterrows():
                    row_str = ' '.join([str(val).upper() for val in row.values if pd.notna(val)])
                    # Buscar cualquier variante de RUN en los encabezados
                    if 'R.U.N' in row_str or 'RUN 1' in row_str or 'RUN1' in row_str or 'RUN_1' in row_str:
                        header_row = idx
                        logger.debug(f"Hoja '{nombre_hoja}': Encabezados encontrados en fila {idx + 1}")
                        break
                
                if header_row is None:
                    # Si no encontramos encabezados explícitos, probar fila 0 y 1
                    logger.warning(f"Hoja '{nombre_hoja}': No se encontró 'R.U.N' en encabezados, probando fila 0")
                    header_row = 0
                
                # Ahora leer el Excel completo con la fila de encabezados detectada
                df = pd.read_excel(
                    ruta, 
                    sheet_name=nombre_hoja, 
                    header=header_row,
                    engine='openpyxl'
                )
                
                if df is not None and not df.empty:
                    # Limpiar nombres de columnas (convertir a string)
                    df.columns = [str(col).strip() if pd.notna(col) else f'Unnamed_{i}' 
                                  for i, col in enumerate(df.columns)]
                    
                    dfs_validos[nombre_hoja] = df
                    logger.info(f"Hoja '{nombre_hoja}': {len(df)} filas, {len(df.columns)} columnas (header en fila {header_row + 1})")
                    logger.debug(f"Hoja '{nombre_hoja}' columnas: {list(df.columns[:10])}...")
                else:
                    logger.warning(f"Hoja '{nombre_hoja}' está vacía")
                    
            except Exception as e:
                logger.warning(f"Error leyendo hoja '{nombre_hoja}': {e}")
                continue
        
        if not dfs_validos:
            logger.error("No se encontraron hojas válidas en el Excel")
            return None
        
        logger.info(f"Total de hojas leídas: {len(dfs_validos)}")
        return dfs_validos
        
    except Exception as e:
        logger.error(f"Error leyendo Excel {ruta}: {e}")
        import traceback
        logger.debug(traceback.format_exc())
        return None


def mapear_columnas(df: pd.DataFrame) -> Dict[str, str]:
    """
    Mapea los nombres de columnas 'sucios' del Excel a campos del modelo.
    Busca coincidencias flexibles.
    
    Args:
        df: DataFrame del Excel
        
    Returns:
        Diccionario {nombre_columna_excel: campo_modelo}
    """
    mapeo = {}
    columnas_excel = df.columns.tolist()
    
    # COLUMN_MAPPING tiene estructura: {"NOMBRE_EXCEL": "campo_modelo"}
    for nombre_excel_esperado, campo_modelo in COLUMN_MAPPING.items():
        nombre_normalizado = normalizar_columna(nombre_excel_esperado)
        
        # Buscar columna que coincida
        for col_excel in columnas_excel:
            col_normalizada = normalizar_columna(col_excel)
            
            # Coincidencia exacta o parcial
            if (col_normalizada == nombre_normalizado or
                col_normalizada.startswith(nombre_normalizado) or
                nombre_normalizado in col_normalizada or
                # Búsqueda flexible por palabras clave
                any(palabra in col_normalizada for palabra in nombre_normalizado.split() if len(palabra) > 3)):
                mapeo[col_excel] = campo_modelo
                logger.debug(f"Mapeado: '{col_excel}' -> {campo_modelo}")
                break
    
    # Verificar que al menos tenemos RUN
    if 'run' not in mapeo.values():
        logger.error("No se encontró columna 'R.U.N 1' en el Excel")
        logger.error(f"Columnas disponibles: {columnas_excel}")
        return {}
    
    return mapeo


def procesar_fila(
    row: pd.Series,
    column_mapping: Dict[str, str],
    session: Any,
    usuario: str = None
) -> Tuple[bool, str, Optional[str]]:
    """
    Procesa una fila del Excel (Upsert: Insert o Update).
    
    Args:
        row: Serie de pandas con los datos de la fila
        column_mapping: Mapeo de columnas Excel -> modelo
        session: Sesión de SQLAlchemy
        usuario: Usuario que realiza la sincronización
        
    Returns:
        Tuple (exito, mensaje, run)
    """
    try:
        # 1. Extraer y limpiar RUN
        col_run_excel = None
        for col, campo in column_mapping.items():
            if campo == 'run':
                col_run_excel = col
                break
        
        if not col_run_excel:
            return False, "Columna RUN no encontrada", None
        
        run_raw = row.get(col_run_excel)
        run = limpiar_run(run_raw)
        
        if not run:
            return False, f"RUN inválido o vacío: {run_raw}", None
        
        # 2. Extraer otros campos (column_mapping es {nombre_col_excel: campo_modelo})
        # Función auxiliar para obtener valor desde el mapeo
        def obtener_valor(campo_modelo: str, default: Any = '') -> str:
            """Busca la columna Excel que mapea a campo_modelo y retorna su valor."""
            for col_excel, campo in column_mapping.items():
                if campo == campo_modelo:
                    valor = row.get(col_excel, default)
                    # Manejar valores nulos o NaN
                    if valor is None or pd.isna(valor):
                        return default
                    # Convertir a string de forma segura (maneja datetime, int, float, etc.)
                    valor_str = str(valor)
                    # Verificar si es 'nan' o vacío después de convertir
                    if valor_str.strip().lower() == 'nan' or valor_str.strip() == '':
                        return default
                    return valor_str.strip()
            return default
        
        nombres = obtener_valor('nombres', '')
        paterno = obtener_valor('paterno', '')
        materno = obtener_valor('materno', '')
        carrera = obtener_valor('carrera', '')
        profesor_guia_raw = obtener_valor('profesor_guia', None)
        profesor_guia = profesor_guia_raw if profesor_guia_raw else None
        titulo_proyecto_raw = obtener_valor('titulo_proyecto', None)
        # Limpiar y validar título - no usar None si está vacío, usar None solo si realmente no existe
        if titulo_proyecto_raw and str(titulo_proyecto_raw).strip() and str(titulo_proyecto_raw).strip() != 'nan':
            titulo_proyecto = str(titulo_proyecto_raw).strip()
        else:
            titulo_proyecto = None
        semestre = obtener_valor('semestre', '')
        estado_excel = obtener_valor('estado', None)
        
        # Validar campos requeridos
        if not nombres or nombres == 'nan':
            return False, f"Fila sin nombres válidos (RUN: {run})", run
        
        # Concatenar apellidos
        apellidos = f"{paterno} {materno}".strip()
        if not apellidos or apellidos == 'nan':
            return False, f"Fila sin apellidos válidos (RUN: {run})", run
        
        if not carrera or carrera == 'nan':
            return False, f"Fila sin carrera válida (RUN: {run})", run
        
        if not semestre or semestre == 'nan':
            return False, f"Fila sin semestre válido (RUN: {run})", run
        
        # Mapear estado
        estado = mapear_estado_excel(estado_excel)
        
        # 3. Buscar estudiante existente
        estudiante = session.query(Estudiante).filter(Estudiante.run == run).first()
        
        if estudiante:
            # CASO 2: Estudiante existe - Actualizar solo campos permitidos
            logger.debug(f"Actualizando estudiante existente: {run}")
            
            # Actualizar datos básicos del estudiante (solo si cambiaron)
            actualizado = False
            if estudiante.nombres != nombres:
                estudiante.nombres = nombres
                actualizado = True
            if estudiante.apellidos != apellidos:
                estudiante.apellidos = apellidos
                actualizado = True
            if estudiante.carrera != carrera:
                estudiante.carrera = carrera
                actualizado = True
            
            if actualizado:
                estudiante.updated_at = datetime.now()
                # Log deshabilitado temporalmente durante sync masivo para evitar timeouts
                # log_user_action(
                #     tabla="estudiantes",
                #     registro_id=run,
                #     accion="UPDATE",
                #     usuario=usuario,
                #     descripcion=f"Actualizado desde Excel: {nombres} {apellidos}",
                #     valores_nuevos=f'{{"nombres": "{nombres}", "apellidos": "{apellidos}", "carrera": "{carrera}"}}'
                # )
        else:
            # CASO 1: Estudiante nuevo - Crear
            logger.debug(f"Creando nuevo estudiante: {run}")
            estudiante = Estudiante(
                run=run,
                nombres=nombres,
                apellidos=apellidos,
                carrera=carrera,
                modalidad=DEFAULT_MODALIDAD_ESTUDIANTE
            )
            session.add(estudiante)
            # Log deshabilitado temporalmente durante sync masivo para evitar timeouts
            # log_user_action(
            #     tabla="estudiantes",
            #     registro_id=run,
            #     accion="CREATE",
            #     usuario=usuario,
            #     descripcion=f"Creado desde Excel: {nombres} {apellidos}",
            #     valores_nuevos=f'{{"run": "{run}", "nombres": "{nombres}", "apellidos": "{apellidos}", "carrera": "{carrera}"}}'
            # )
        
        # Flush para asegurar que el estudiante esté en BD antes de crear proyecto
        session.flush()
        
        # 4. Buscar o crear Proyecto para este estudiante y semestre
        proyecto = session.query(Proyecto).filter(
            Proyecto.estudiante_run1 == run,
            Proyecto.semestre == semestre
        ).first()
        
        if proyecto:
            # Proyecto existe - Actualizar solo campos permitidos
            # Actualizar título si:
            # 1. Hay un título nuevo Y el proyecto no tiene título, O
            # 2. Hay un título nuevo Y es diferente al existente
            if titulo_proyecto:
                if not proyecto.titulo or proyecto.titulo.strip() == '' or proyecto.titulo != titulo_proyecto:
                    proyecto.titulo = titulo_proyecto
                    proyecto.updated_at = datetime.now()
                    logger.debug(f"Actualizado título del proyecto {proyecto.id}: '{titulo_proyecto}'")
        else:
            # Proyecto nuevo - Crear
            proyecto = Proyecto(
                estudiante_run1=run,
                semestre=semestre,
                modalidad_titulacion=DEFAULT_MODALIDAD_TITULACION,
                titulo=titulo_proyecto
            )
            session.add(proyecto)
            session.flush()
        
        # 5. Buscar o crear Comision para este proyecto
        comision = session.query(Comision).filter(
            Comision.proyecto_id == proyecto.id
        ).first()
        
        if comision:
            # Comision existe - Actualizar profesor guía si cambió
            if profesor_guia and comision.profesor_guia != profesor_guia:
                comision.profesor_guia = profesor_guia
        else:
            # Comision nueva - Crear
            comision = Comision(
                proyecto_id=proyecto.id,
                profesor_guia=profesor_guia
            )
            session.add(comision)
            session.flush()
        
        # 6. Buscar o crear Expediente para este proyecto
        expediente = session.query(Expediente).filter(
            Expediente.proyecto_id == proyecto.id
        ).first()
        
        if expediente:
            # Expediente existe - Actualizar estado si cambió
            if expediente.estado != estado:
                expediente.estado = estado
                expediente.updated_at = datetime.now()
        else:
            # Expediente nuevo - Crear
            expediente = Expediente(
                proyecto_id=proyecto.id,
                estado=estado
            )
            session.add(expediente)
        
        return True, f"Fila procesada exitosamente", run
        
    except Exception as e:
        logger.error(f"Error procesando fila: {e}")
        import traceback
        logger.debug(traceback.format_exc())
        return False, f"Error: {str(e)}", None


def sincronizar_excel(
    ruta_excel: str = EXCEL_PATH,
    usuario: str = None,
    hojas: List[str] = None
) -> Dict[str, Any]:
    """
    Función principal de sincronización (ETL completo).
    Procesa múltiples hojas del Excel.
    
    Args:
        ruta_excel: Ruta al archivo Excel (default: EXCEL_PATH)
        usuario: Usuario que realiza la sincronización
        hojas: Lista de hojas a procesar (default: HOJAS_EXCEL)
        
    Returns:
        Diccionario con resultados:
        {
            "success": bool,
            "total_filas": int,
            "procesadas": int,
            "errores": int,
            "hojas_procesadas": int,
            "detalles": Dict con resultados por hoja
        }
    """
    if hojas is None:
        hojas = HOJAS_EXCEL
    
    resultado = {
        "success": False,
        "total_filas": 0,
        "procesadas": 0,
        "errores": 0,
        "hojas_procesadas": 0,
        "detalles": {}
    }
    
    try:
        # 1. Leer Excel (todas las hojas)
        logger.info(f"Iniciando sincronización desde Excel: {ruta_excel}")
        logger.info(f"Hojas a procesar: {hojas}")
        
        dfs_por_hoja = leer_excel(ruta_excel, hojas)
        
        if dfs_por_hoja is None or len(dfs_por_hoja) == 0:
            resultado["detalles"]["error"] = {
                "tipo": "error",
                "mensaje": "No se pudo leer el Excel o no se encontraron hojas válidas"
            }
            return resultado
        
        # 2. Procesar cada hoja
        errores_totales = []
        procesadas_totales = []
        resultados_por_hoja = {}
        
        with get_session_context() as session:
            for nombre_hoja, df in dfs_por_hoja.items():
                logger.info(f"Procesando hoja: {nombre_hoja}")
                
                # Mapear columnas para esta hoja
                column_mapping = mapear_columnas(df)
                if not column_mapping or 'run' not in column_mapping.values():
                    logger.warning(f"Hoja '{nombre_hoja}': No se pudo mapear columnas. Saltando...")
                    resultados_por_hoja[nombre_hoja] = {
                        "procesadas": 0,
                        "errores": len(df),
                        "mensaje": "No se pudo mapear las columnas. Verifica que tenga la columna 'R.U.N 1'"
                    }
                    resultado["errores"] += len(df)
                    resultado["total_filas"] += len(df)
                    continue
                
                logger.info(f"Hoja '{nombre_hoja}': Columnas mapeadas: {len(column_mapping)}")
                
                # Procesar cada fila de esta hoja
                errores_hoja = []
                procesadas_hoja = []
                
                for index, row in df.iterrows():
                    exito, mensaje, run = procesar_fila(row, column_mapping, session, usuario)
                    
                    if exito:
                        resultado["procesadas"] += 1
                        procesadas_hoja.append({
                            "fila": index + 2,  # +2 porque Excel tiene fila de título y encabezados
                            "run": run,
                            "mensaje": mensaje
                        })
                        logger.debug(f"Hoja '{nombre_hoja}', Fila {index + 2}: {mensaje}")
                    else:
                        resultado["errores"] += 1
                        errores_hoja.append({
                            "fila": index + 2,
                            "run": run or "N/A",
                            "mensaje": mensaje
                        })
                        logger.warning(f"Hoja '{nombre_hoja}', Fila {index + 2}: {mensaje}")
                
                resultado["total_filas"] += len(df)
                resultado["hojas_procesadas"] += 1
                
                # Guardar resultados de esta hoja
                resultados_por_hoja[nombre_hoja] = {
                    "procesadas": len(procesadas_hoja),
                    "errores": len(errores_hoja),
                    "total_filas": len(df),
                    "detalles_procesadas": procesadas_hoja[:5],  # Primeras 5 exitosas
                    "detalles_errores": errores_hoja[:5]  # Primeros 5 errores
                }
                
                procesadas_totales.extend(procesadas_hoja)
                errores_totales.extend(errores_hoja)
                
                logger.info(
                    f"Hoja '{nombre_hoja}' completada: {len(procesadas_hoja)} procesadas, "
                    f"{len(errores_hoja)} errores de {len(df)} totales"
                )
            
            # El commit se hace automáticamente al salir del context manager
        
        # 4. Compilar resultados finales
        resultado["success"] = True
        resultado["detalles"] = {
            "por_hoja": resultados_por_hoja,
            "resumen": {
                "procesadas": procesadas_totales[:10],  # Primeras 10 exitosas totales
                "errores": errores_totales[:10]  # Primeros 10 errores totales
            }
        }
        
        logger.info(
            f"Sincronización completada: {resultado['hojas_procesadas']} hojas procesadas, "
            f"{resultado['procesadas']} filas procesadas, "
            f"{resultado['errores']} errores de {resultado['total_filas']} filas totales"
        )
        
        return resultado
        
    except Exception as e:
        logger.error(f"Error crítico en sincronización: {e}")
        import traceback
        resultado["detalles"]["error_critico"] = {
            "tipo": "error_critico",
            "mensaje": str(e),
            "traceback": traceback.format_exc()
        }
        return resultado
