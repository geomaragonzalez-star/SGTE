# Ficha Técnica - Sistema de Gestión de Titulaciones y Expedientes (SGTE)

**Versión:** 2.0.0  
**Fecha:** Enero 2026  
**Arquitectura:** FastAPI + Jinja2 Templates  
**Base de Datos:** SQLite  
**Lenguaje:** Python 3.12+

---

## 📋 Índice

1. [Descripción General](#descripción-general)
2. [Arquitectura del Sistema](#arquitectura-del-sistema)
3. [Estructura del Proyecto](#estructura-del-proyecto)
4. [Modelo de Datos](#modelo-de-datos)
5. [Funcionalidades Implementadas](#funcionalidades-implementadas)
6. [API Endpoints](#api-endpoints)
7. [Interfaz de Usuario](#interfaz-de-usuario)
8. [Servicios y Módulos](#servicios-y-módulos)
9. [Configuración e Instalación](#configuración-e-instalación)
10. [Dependencias](#dependencias)

---

## 🎯 Descripción General

**SGTE** (Sistema de Gestión de Titulaciones y Expedientes) es una aplicación web desarrollada para digitalizar y automatizar el flujo de trabajo de la Secretaría Docente del Departamento de Ingeniería Industrial de la Universidad de Santiago de Chile (USACH).

El sistema centraliza la información de estudiantes en proceso de titulación, gestiona la recolección de documentos habilitantes (Bienestar, Finanzas, Biblioteca, SDT) y automatiza la solicitud de apertura de expediente a Registro Curricular.

### Objetivos Principales

- **Digitalización:** Reemplazar procesos manuales basados en Excel y correos electrónicos
- **Automatización:** Generación masiva de documentos y envío de correos
- **Centralización:** Base de datos única como fuente de verdad
- **Eficiencia:** Procesamiento por lotes para gestionar altos volúmenes de solicitudes

---

## 🏗️ Arquitectura del Sistema

### Stack Tecnológico

- **Backend:** FastAPI 0.104.0+
- **Frontend:** Jinja2 Templates + TailwindCSS + JavaScript vanilla
- **Base de Datos:** SQLite 3 (con SQLAlchemy ORM 2.0+)
- **Servidor:** Uvicorn (ASGI)
- **Procesamiento:** Python 3.12+

### Patrón de Arquitectura

```
┌─────────────────────────────────────────┐
│         Frontend (Jinja2)                │
│  - Templates HTML                      │
│  - CSS (TailwindCSS)                    │
│  - JavaScript (Vanilla)                 │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│      FastAPI Backend (API Routes)        │
│  - /api/estudiantes                     │
│  - /api/documentos                      │
│  - /api/expedientes                     │
│  - /api/reportes                        │
│  - /api/dashboard                       │
│  - /api/operaciones                     │
│  - /api/pdf-splitter                    │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│      Capa de Servicios (Business Logic)  │
│  - estudiantes.py                       │
│  - excel_export.py                       │
│  - memo_generator.py                     │
│  - pdf_splitter.py                      │
│  - email_queue.py                       │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│      Capa de Datos (SQLAlchemy ORM)      │
│  - models.py (Entidades)                │
│  - connection.py (Gestión de sesiones)   │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│      SQLite Database (sgte.db)          │
└──────────────────────────────────────────┘
```

### Características de Diseño

- **Arquitectura de Escritorio con Persistencia Centralizada:** La aplicación se ejecuta localmente pero la base de datos se aloja en una unidad de red compartida (OneDrive/Google Drive)
- **Sin Dependencias de Servidor Externo:** Todo funciona localmente
- **Integración con Outlook:** Envío automático de correos mediante cliente local
- **Procesamiento por Lotes:** Operaciones masivas para eficiencia

---

## 📁 Estructura del Proyecto

```
SGTE/
├── assets/                          # Recursos estáticos (logos)
│   ├── logo_departamento.png
│   └── logo-web2025-b.png
│
├── backend/                         # Backend FastAPI
│   └── api/
│       ├── main.py                 # Aplicación principal FastAPI
│       └── routes/                  # Endpoints de la API
│           ├── estudiantes.py      # CRUD estudiantes
│           ├── documentos.py       # Gestión de documentos
│           ├── expedientes.py      # Gestión de expedientes
│           ├── reportes.py         # Generación de reportes
│           ├── dashboard.py        # Métricas y estadísticas
│           ├── operaciones.py      # Operaciones masivas
│           └── pdf_splitter.py    # Procesamiento de PDFs
│
├── database/                        # Capa de datos
│   ├── models.py                   # Modelos SQLAlchemy
│   ├── connection.py               # Gestión de conexiones
│   └── connection_optimized.py    # Conexión optimizada
│
├── data/                           # Datos del sistema
│   ├── sgte.db                     # Base de datos SQLite
│   └── expedientes/               # Archivos PDF por estudiante
│       └── {RUN}/
│           └── *.pdf
│
├── frontend/                       # Frontend
│   ├── static/
│   │   ├── css/
│   │   │   └── main.css           # Estilos personalizados
│   │   └── js/
│   │       └── main.js            # JavaScript del cliente
│   └── templates/                  # Templates Jinja2
│       ├── base.html              # Template base
│       ├── index.html             # Página de inicio
│       ├── dashboard.html          # Dashboard principal
│       ├── error.html             # Página de error
│       ├── estudiantes/           # Vistas de estudiantes
│       │   ├── lista.html
│       │   ├── crear.html
│       │   ├── detalle.html
│       │   └── editar.html
│       ├── documentos/            # Vistas de documentos
│       │   ├── lista.html
│       │   └── detalle.html
│       ├── operaciones/          # Operaciones masivas
│       │   └── lista.html
│       └── pdf_splitter/         # PDF Splitter
│           └── index.html
│
├── services/                      # Lógica de negocio
│   ├── estudiantes.py            # Servicios de estudiantes
│   ├── excel_export.py           # Exportación a Excel
│   ├── memo_generator.py         # Generación de memorándums
│   ├── pdf_splitter.py          # Procesamiento de PDFs
│   ├── pdf_splitter_optimized.py # Versión optimizada
│   └── email_queue.py            # Cola de envío de correos
│
├── logs/                         # Archivos de log
│   └── sgte_YYYY-MM-DD.log
│
├── config.py                     # Configuración centralizada
├── requirements.txt              # Dependencias generales
├── requirements_backend.txt     # Dependencias del backend
├── install.bat                  # Script de instalación
├── iniciar_sgte.bat            # Lanzador principal (.bat)
├── iniciar_sgte.vbs             # Lanzador principal (.vbs - sin ventana)
├── iniciar_servidor.py          # Script Python de inicio
└── iniciar_backend.bat          # Lanzador alternativo
```

---

## 🗄️ Modelo de Datos

### Entidades Principales

#### 1. **Estudiante**
- **Clave Primaria:** `run` (String, 12 caracteres)
- **Campos:**
  - `nombres`, `apellidos`, `nombre_completo`
  - `carrera`, `email`, `modalidad`
  - `created_at`, `updated_at`
- **Relaciones:** 
  - Uno a muchos con `Proyecto`
  - Uno a muchos con `Documento`
  - Uno a uno con `Expediente`

#### 2. **Proyecto**
- **Clave Primaria:** `id` (Integer, auto-incremental)
- **Clave Foránea:** `estudiante_run` → `Estudiante.run`
- **Campos:**
  - `titulo_proyecto`, `link_documento`
  - `semestre`, `modalidad` (Enum)
  - `profesor_guia`, `profesor_corrector_1`, `profesor_corrector_2`
  - `fecha_registro`

#### 3. **Expediente**
- **Clave Primaria:** `id` (Integer)
- **Clave Foránea:** `estudiante_run` → `Estudiante.run`
- **Campos:**
  - `estado` (Enum: PENDIENTE, EN_PROCESO, LISTO_ENVIO, ENVIADO, APROBADO, TITULADO)
  - `observaciones`, `titulado` (Boolean)
  - `semestre_titulacion`
  - `created_at`, `updated_at`

#### 4. **Documento**
- **Clave Primaria:** `id` (Integer)
- **Clave Foránea:** `estudiante_run` → `Estudiante.run`
- **Campos:**
  - `tipo` (Enum: BIENESTAR, FINANZAS_TITULO, FINANZAS_LICENCIA, BIBLIOTECA, SDT, MEMORANDUM, ACTA, OTRO)
  - `path` (ruta al archivo PDF)
  - `validado` (Boolean)
  - `validated_at`, `validated_by`
  - `uploaded_at`

#### 5. **Hito**
- **Clave Primaria:** `id` (Integer)
- **Clave Foránea:** `expediente_id` → `Expediente.id`
- **Campos:**
  - `tipo` (Enum: NOTIFICACION_COMISION, ENTREGA_AVANCE, PRESENTACION_AVANCE, ENTREGA_DOC_FINAL, ACEPTACION_BIBLIOTECA, EXAMEN_GRADO)
  - `fecha`, `completado` (Boolean)

#### 6. **Bitácora**
- **Clave Primaria:** `id` (Integer)
- **Campos:**
  - `tabla`, `registro_id`, `accion` (String)
  - `usuario`, `descripcion`
  - `timestamp`

### Enumeraciones (Enums)

- **EstadoExpediente:** PENDIENTE, EN_PROCESO, LISTO_ENVIO, ENVIADO, APROBADO, TITULADO
- **ModalidadProyecto:** TESIS, PROYECTO, SEMINARIO, PRACTICA, EXAMEN
- **TipoDocumento:** BIENESTAR, FINANZAS_TITULO, FINANZAS_LICENCIA, BIBLIOTECA, SDT, MEMORANDUM, ACTA, OTRO
- **TipoHito:** NOTIFICACION_COMISION, ENTREGA_AVANCE, PRESENTACION_AVANCE, ENTREGA_DOC_FINAL, ACEPTACION_BIBLIOTECA, EXAMEN_GRADO

---

## ⚙️ Funcionalidades Implementadas

### 1. Gestión de Estudiantes (RF-01)

**Descripción:** CRUD completo para estudiantes.

**Funcionalidades:**
- ✅ Crear nuevo estudiante con validación de RUN chileno
- ✅ Buscar estudiantes por RUN o nombre
- ✅ Editar información de estudiantes
- ✅ Eliminar estudiantes
- ✅ Listar estudiantes con paginación
- ✅ Filtrar por carrera y modalidad
- ✅ Verificar si estudiante está listo para expediente

**Endpoints:**
- `GET /api/estudiantes` - Listar estudiantes
- `GET /api/estudiantes/{run}` - Obtener estudiante
- `POST /api/estudiantes` - Crear estudiante
- `PUT /api/estudiantes/{run}` - Actualizar estudiante
- `DELETE /api/estudiantes/{run}` - Eliminar estudiante
- `GET /api/estudiantes/carreras/lista` - Listar carreras
- `GET /api/estudiantes/checklist-status` - Estado de checklist por RUNs

**Vistas Frontend:**
- `/estudiantes` - Lista de estudiantes con filtros
- `/estudiantes/nuevo` - Formulario de creación
- `/estudiantes/{run}` - Detalle del estudiante
- `/estudiantes/{run}/editar` - Formulario de edición

### 2. Gestión de Documentos (RF-02)

**Descripción:** Carga, validación y gestión de documentos habilitantes.

**Documentos Requeridos:**
1. **Bienestar Estudiantil** - Certificado de no deuda
2. **Finanzas (Título)** o **Finanzas (Licenciatura)** - Certificado financiero
3. **Biblioteca** - Constancia de aceptación
4. **SDT (Secretaría Docente)** - Documento institucional
5. **Memorándum de Solicitud** - Solicitud de apertura

**Funcionalidades:**
- ✅ Subir documentos PDF por estudiante
- ✅ Validar documentos
- ✅ Previsualizar documentos en el navegador
- ✅ Eliminar documentos
- ✅ Checklist de documentos requeridos
- ✅ Verificación automática de completitud
- ✅ Indicador de "Listo para Expediente"

**Endpoints:**
- `GET /api/documentos` - Listar documentos
- `GET /api/documentos/estudiante/{run}` - Documentos de un estudiante
- `GET /api/documentos/checklist/{run}` - Checklist detallado
- `POST /api/documentos/upload` - Subir documento
- `GET /api/documentos/{doc_id}/preview` - Previsualizar PDF
- `DELETE /api/documentos/{doc_id}` - Eliminar documento
- `PUT /api/documentos/{doc_id}/validar` - Validar documento

**Vistas Frontend:**
- `/informaciones` - Información sobre documentos requeridos
- `/documentos/{run}` - Documentos de un estudiante específico

### 3. Dashboard y Métricas

**Descripción:** Panel de control con estadísticas y resumen del sistema.

**Funcionalidades:**
- ✅ Métricas principales (total estudiantes, proyectos, enviados, titulados)
- ✅ Semáforo de estados de expedientes
- ✅ Distribución por carrera
- ✅ Últimos registros
- ✅ Estadísticas del sistema
- ✅ Información de base de datos

**Endpoints:**
- `GET /api/dashboard/metricas` - Obtener métricas
- `GET /api/dashboard/distribucion-carreras` - Distribución por carrera
- `GET /api/dashboard/ultimos-registros` - Últimos estudiantes registrados

**Vista Frontend:**
- `/dashboard` - Dashboard principal con todas las métricas y reportes

### 4. Reportes y Exportación (RF-06)

**Descripción:** Generación de reportes en Excel y respaldo de base de datos.

**Funcionalidades:**
- ✅ Reporte Maestro (todos los datos en formato institucional)
- ✅ Lista de Estudiantes (directorio completo)
- ✅ Bitácora de Acciones (historial del sistema)
- ✅ Descarga de respaldo de base de datos
- ✅ Estadísticas del sistema

**Endpoints:**
- `GET /api/reportes/maestro` - Generar reporte maestro (.xlsx)
- `GET /api/reportes/estudiantes` - Exportar estudiantes (.xlsx)
- `GET /api/reportes/bitacora` - Exportar bitácora (.xlsx)
- `GET /api/reportes/estadisticas` - Estadísticas generales
- `GET /api/reportes/backup` - Descargar respaldo BD (.db)

**Vista Frontend:**
- Integrado en `/dashboard` - Sección "Reportes y Exportación"

### 5. Operaciones Masivas (RF-04, RF-05)

**Descripción:** Procesamiento por lotes para múltiples estudiantes.

**Funcionalidades:**
- ✅ Generación masiva de memorándums
- ✅ Envío masivo de correos a Registro Curricular
- ✅ Cambio masivo de estado de expedientes
- ✅ Verificación de conexión con Outlook

**Endpoints:**
- `POST /api/operaciones/generar-memos` - Generar memorándums masivos
- `POST /api/operaciones/enviar-correos` - Enviar correos masivos
- `POST /api/operaciones/cambiar-estado` - Cambiar estado masivo
- `GET /api/operaciones/verificar-outlook` - Verificar Outlook

**Vista Frontend:**
- `/operaciones-masivas` - Interfaz para operaciones masivas

### 6. PDF Splitter (RF-03)

**Descripción:** Procesamiento inteligente de PDFs masivos con OCR.

**Funcionalidades:**
- ✅ Carga de PDF único masivo
- ✅ Detección automática de RUN/Nombre mediante OCR
- ✅ Separación de páginas por estudiante
- ✅ Asignación automática a carpetas de estudiantes

**Endpoints:**
- `GET /api/pdf-splitter/verificar` - Verificar estado
- `POST /api/pdf-splitter/procesar` - Procesar PDF masivo

**Vista Frontend:**
- `/pdf-splitter` - Interfaz para procesamiento de PDFs

### 7. Gestión de Expedientes

**Descripción:** Control del ciclo de vida de expedientes.

**Funcionalidades:**
- ✅ Crear expediente para estudiante
- ✅ Actualizar estado del expediente
- ✅ Ver estadísticas de expedientes
- ✅ Gestión de hitos del proceso

**Endpoints:**
- `GET /api/expedientes` - Listar expedientes
- `GET /api/expedientes/estadisticas` - Estadísticas
- `PUT /api/expedientes/{expediente_id}` - Actualizar expediente

---

## 🔌 API Endpoints Completos

### Estudiantes
```
GET    /api/estudiantes                    # Listar estudiantes
GET    /api/estudiantes/{run}              # Obtener estudiante
POST   /api/estudiantes                    # Crear estudiante
PUT    /api/estudiantes/{run}              # Actualizar estudiante
DELETE /api/estudiantes/{run}              # Eliminar estudiante
GET    /api/estudiantes/carreras/lista     # Listar carreras
GET    /api/estudiantes/checklist-status   # Estado de checklist
```

### Documentos
```
GET    /api/documentos                     # Listar documentos
GET    /api/documentos/estudiante/{run}   # Documentos de estudiante
GET    /api/documentos/checklist/{run}     # Checklist detallado
POST   /api/documentos/upload              # Subir documento
GET    /api/documentos/{doc_id}/preview    # Previsualizar PDF
DELETE /api/documentos/{doc_id}            # Eliminar documento
PUT    /api/documentos/{doc_id}/validar    # Validar documento
```

### Expedientes
```
GET    /api/expedientes                    # Listar expedientes
GET    /api/expedientes/estadisticas       # Estadísticas
PUT    /api/expedientes/{expediente_id}    # Actualizar expediente
```

### Reportes
```
GET    /api/reportes/maestro               # Reporte maestro (.xlsx)
GET    /api/reportes/estudiantes           # Exportar estudiantes (.xlsx)
GET    /api/reportes/bitacora               # Exportar bitácora (.xlsx)
GET    /api/reportes/estadisticas           # Estadísticas generales
GET    /api/reportes/backup                 # Respaldo BD (.db)
```

### Dashboard
```
GET    /api/dashboard/metricas             # Métricas principales
GET    /api/dashboard/distribucion-carreras # Distribución por carrera
GET    /api/dashboard/ultimos-registros    # Últimos registros
```

### Operaciones Masivas
```
POST   /api/operaciones/generar-memos      # Generar memorándums masivos
POST   /api/operaciones/enviar-correos     # Enviar correos masivos
POST   /api/operaciones/cambiar-estado    # Cambiar estado masivo
GET    /api/operaciones/verificar-outlook  # Verificar Outlook
```

### PDF Splitter
```
GET    /api/pdf-splitter/verificar         # Verificar estado
POST   /api/pdf-splitter/procesar          # Procesar PDF masivo
```

### Frontend (Rutas HTML)
```
GET    /                                   # Página de inicio
GET    /dashboard                          # Dashboard principal
GET    /estudiantes                        # Lista de estudiantes
GET    /estudiantes/nuevo                  # Crear estudiante
GET    /estudiantes/{run}                  # Detalle estudiante
GET    /estudiantes/{run}/editar           # Editar estudiante
GET    /informaciones                      # Información de documentos
GET    /documentos                         # Gestión de documentos
GET    /documentos/{run}                   # Documentos de estudiante
GET    /operaciones-masivas                # Operaciones masivas
GET    /pdf-splitter                       # PDF Splitter
GET    /health                             # Health check
```

---

## 🎨 Interfaz de Usuario

### Diseño

- **Framework CSS:** TailwindCSS
- **Iconos:** Font Awesome
- **Responsive:** Diseño adaptativo para móviles y tablets
- **Tema:** Modo claro con sidebar oscuro

### Componentes Principales

#### Sidebar de Navegación
- **Estado:** Colapsable/Expandible
- **Elementos:**
  - Inicio
  - Dashboard
  - Estudiantes
  - Operaciones Masivas
  - PDF Splitter
  - Informaciones (en footer)
- **Características:**
  - Resalta opción activa
  - Persistencia de estado (localStorage)
  - Logo y texto "SGTE" siempre visibles

#### Header
- **Contenido:** Solo logo del departamento
- **Sticky:** Fijo en la parte superior
- **Responsive:** Botón de menú para móviles

#### Dashboard
- **Métricas Principales:** 4 tarjetas con estadísticas clave
- **Semáforo de Estados:** 4 indicadores visuales de estado
- **Distribución por Carrera:** Lista de carreras con conteos
- **Últimos Registros:** Lista de estudiantes recientes
- **Reportes y Exportación:** Tarjetas para generar reportes
- **Respaldo de BD:** Información y descarga de respaldo
- **Estadísticas del Sistema:** 4 métricas generales

#### Lista de Estudiantes
- **Tabla:** Con paginación y filtros
- **Filtros:**
  - Por modalidad
  - Por estado "listo para expediente"
  - Por carrera
- **Checklist:** Columna con estado de documentos
- **Acciones:**
  - Ver checklist expandible
  - Editar estudiante
- **Checklist Expandible:**
  - Lista de documentos requeridos
  - Estado de cada documento
  - Subir/Reemplazar documentos
  - Previsualizar documentos
  - Eliminar documentos

### Características de UX

- **Actualización en Tiempo Real:** El checklist se actualiza sin recargar la página
- **Previsualización de PDFs:** Modal con iframe para ver documentos
- **Feedback Visual:** Indicadores de carga, estados de éxito/error
- **Validación de Formularios:** Validación en cliente y servidor
- **Mensajes de Error:** Claros y contextuales

---

## 🔧 Servicios y Módulos

### services/estudiantes.py
**Funciones principales:**
- `crear_estudiante()` - Crear nuevo estudiante
- `obtener_estudiante(run)` - Obtener por RUN
- `buscar_estudiantes()` - Búsqueda con filtros
- `actualizar_estudiante()` - Actualizar datos
- `eliminar_estudiante()` - Eliminar estudiante
- `obtener_carreras()` - Listar carreras únicas
- `validar_run()` - Validar formato y dígito verificador
- `formatear_run()` - Formatear RUN con puntos y guión

### services/excel_export.py
**Funciones principales:**
- `exportar_estudiantes()` - Exportar lista de estudiantes
- `generar_reporte_maestro()` - Reporte completo institucional
- `obtener_datos_completos()` - Datos completos para exportación

### services/memo_generator.py
**Funciones principales:**
- `generar_memorandum()` - Generar memorándum individual
- `generar_memorandums_masivos()` - Generación por lotes
- Plantilla DOCX con datos del estudiante

### services/pdf_splitter.py
**Funciones principales:**
- `procesar_pdf_masivo()` - Procesar PDF con múltiples estudiantes
- `extraer_texto_ocr()` - Extracción de texto con OCR
- `detectar_run_nombre()` - Detección automática de RUN/Nombre
- `separar_paginas()` - Separación por estudiante

### services/email_queue.py
**Funciones principales:**
- `enviar_correo_registro()` - Enviar correo individual
- `procesar_cola_envios()` - Procesamiento masivo
- Integración con Outlook mediante `win32com.client`

### database/connection.py
**Funciones principales:**
- `get_session_context()` - Context manager para sesiones SQLAlchemy
- `log_user_action()` - Registrar acciones en bitácora
- Manejo de transacciones y errores

---

## ⚙️ Configuración e Instalación

### Requisitos Previos

- Python 3.12 o superior
- Windows 10/11 (para integración con Outlook)
- Acceso a unidad de red compartida (OneDrive/Google Drive)
- Microsoft Outlook instalado (para envío de correos)

### Instalación

1. **Clonar o descargar el proyecto**
2. **Ejecutar instalador:**
   ```batch
   install.bat
   ```
   Este script:
   - Verifica Python
   - Crea entorno virtual
   - Instala dependencias
   - Configura estructura de directorios

3. **Configurar rutas** (opcional):
   - Editar `config.py` o crear archivo de secrets
   - Configurar rutas de base de datos y expedientes

### Inicio del Sistema

**Opción 1: Lanzador principal (recomendado)**
- Doble clic en `INICIAR_SGTE.vbs`
- Se ejecuta sin mostrar ventanas
- Abre navegador automáticamente en `http://localhost:8000`

**Opción 2: Lanzador alternativo**
- Doble clic en `iniciar_sgte.bat`
- Usa PowerShell para ocultar ventanas

**Opción 3: Manual**
```batch
cd venv\Scripts
activate
cd ..\..
python -m uvicorn backend.api.main:app --reload --host 0.0.0.0 --port 8000
```

### Configuración de Base de Datos

La base de datos SQLite se encuentra en:
- **Ruta por defecto:** `./data/sgte.db`
- **Configurable:** En `config.py` o archivo de secrets

### Estructura de Carpetas de Expedientes

Los PDFs se almacenan en:
- **Ruta:** `./data/expedientes/{RUN}/`
- **Formato de nombre:** `{tipo}_{timestamp}.pdf`

---

## 📦 Dependencias

### Backend (requirements_backend.txt)
```
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
python-multipart>=0.0.6
jinja2>=3.1.0
python-jose[cryptography]>=3.3.0
pydantic>=2.5.0
```

### Generales (requirements.txt)
```
streamlit>=1.30.0          # (legacy, mantenido por compatibilidad)
pandas>=2.0.0              # Procesamiento de datos
openpyxl>=3.1.0            # Exportación a Excel
python-docx>=1.0.0         # Generación de memorándums
pymupdf>=1.23.0            # Procesamiento de PDFs y OCR
loguru>=0.7.0              # Sistema de logging
sqlalchemy>=2.0.0          # ORM para base de datos
watchdog>=3.0.0            # Monitoreo de archivos
```

### Dependencias del Sistema
- **Windows:** Para integración con Outlook (`pywin32`)
- **OCR:** PyMuPDF incluye capacidades de OCR básicas

---

## 🔐 Seguridad y Consideraciones

### Base de Datos
- **Tipo:** SQLite (archivo local/compartido)
- **Concurrencia:** Gestión mediante bloqueo de archivos
- **Respaldo:** Exportación continua a Excel y respaldo de BD

### Archivos
- **Almacenamiento:** Sistema de archivos local
- **Organización:** Por RUN de estudiante
- **Validación:** Solo archivos PDF aceptados

### Logging
- **Nivel:** DEBUG en desarrollo, INFO en producción
- **Rotación:** Diaria
- **Retención:** 30 días
- **Ubicación:** `./logs/sgte_YYYY-MM-DD.log`

---

## 📊 Métricas y Rendimiento

### Capacidad
- **Estudiantes:** Ilimitado (limitado por espacio en disco)
- **Documentos:** Múltiples por estudiante
- **Procesamiento Masivo:** Hasta 100+ estudiantes por lote

### Optimizaciones
- **Conexiones DB:** Pool de conexiones optimizado
- **Procesamiento PDF:** Versión optimizada con multiprocessing
- **Envío de Correos:** Delay configurable para evitar bloqueos

---

## 🚀 Próximas Mejoras (Roadmap)

- [ ] Autenticación de usuarios
- [ ] Roles y permisos
- [ ] Notificaciones en tiempo real
- [ ] Dashboard con gráficos interactivos
- [ ] API REST completa con documentación Swagger
- [ ] Integración con sistemas externos
- [ ] Modo offline con sincronización

---

## 📝 Notas Técnicas

### Migración de Streamlit a FastAPI
El sistema fue migrado completamente de Streamlit a FastAPI + Jinja2 para:
- Mayor control sobre el diseño
- Mejor rendimiento
- Arquitectura más escalable
- Separación clara entre frontend y backend

### Compatibilidad
- **Python:** 3.12+
- **Sistema Operativo:** Windows 10/11 (requerido para Outlook)
- **Navegadores:** Chrome, Firefox, Edge (últimas versiones)

---

## 📞 Soporte y Contacto

**Proyecto:** Sistema de Gestión de Titulaciones y Expedientes (SGTE)  
**Departamento:** Ingeniería Industrial - USACH  
**Versión:** 2.0.0  
**Última Actualización:** Enero 2026

---

**Documento generado automáticamente**  
*Para actualizaciones, consultar el código fuente y los commits del repositorio.*
