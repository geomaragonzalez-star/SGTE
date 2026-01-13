# 📋 REPORTE COMPLETO DE ARQUITECTURA - SGTE v2.0

**Sistema de Gestión de Titulaciones y Expedientes**  
**Fecha:** 13 de Enero, 2025  
**Versión:** 2.0.0

---

## 📁 1. ESTRUCTURA DE DIRECTORIOS

```
SGTE/
├── backend/                    # Backend FastAPI
│   └── api/
│       ├── main.py            # Aplicación FastAPI principal
│       └── routes/            # Endpoints API organizados por dominio
│           ├── estudiantes.py
│           ├── proyectos.py
│           ├── documentos.py
│           ├── expedientes.py
│           ├── operaciones.py
│           ├── reportes.py
│           └── dashboard.py
│
├── frontend/                   # Frontend (Jinja2 + JavaScript)
│   ├── templates/             # Templates HTML con Jinja2
│   │   ├── base.html          # Template base con sidebar
│   │   ├── index.html
│   │   ├── dashboard.html
│   │   ├── estudiantes/      # Vistas de estudiantes
│   │   │   ├── lista.html
│   │   │   ├── crear.html
│   │   │   ├── detalle.html
│   │   │   └── editar.html
│   │   ├── proyectos/
│   │   │   └── lista.html
│   │   ├── documentos/
│   │   │   ├── lista.html
│   │   │   └── detalle.html
│   │   ├── operaciones/
│   │   │   └── lista.html    # Operaciones masivas + PDF Splitter
│   │   └── reportes/
│   │       └── lista.html
│   └── static/               # Archivos estáticos
│       ├── css/
│       │   └── main.css      # Estilos personalizados
│       └── js/
│           └── main.js       # Helper API y utilidades
│
├── services/                  # Lógica de negocio (capa de servicios)
│   ├── estudiantes.py        # CRUD estudiantes
│   ├── excel_export.py       # Exportación a Excel
│   ├── memo_generator.py     # Generación de memorándums
│   ├── pdf_splitter_optimized.py  # Procesamiento de PDFs
│   ├── sync_excel.py         # Sincronización Excel → SQLite
│   └── email_queue.py        # Cola de envío de correos
│
├── database/                 # Capa de datos
│   ├── models.py            # Modelos SQLAlchemy (ORM)
│   ├── connection.py        # Gestión de conexiones y sesiones
│   └── __init__.py         # Exports centralizados
│
├── data/                    # Datos del sistema
│   ├── sgte.db             # Base de datos SQLite
│   └── expedientes/        # Archivos PDF por estudiante
│       └── {RUN}/
│           └── *.pdf
│
├── assets/                  # Recursos estáticos
│   ├── logo_departamento.png
│   └── logo-web2025-b.png
│
├── logs/                    # Archivos de log
│   └── sgte_YYYY-MM-DD.log
│
├── config.py               # Configuración centralizada
├── requirements.txt        # Dependencias generales
├── requirements_backend.txt # Dependencias del backend
└── iniciar_servidor.py     # Script de inicio
```

---

## 🏗️ 2. ARQUITECTURA GENERAL

### 2.1 Patrón Arquitectónico

**Arquitectura en Capas (Layered Architecture):**

```
┌─────────────────────────────────────┐
│   FRONTEND (Presentación)           │
│   - Jinja2 Templates                │
│   - JavaScript Vanilla               │
│   - TailwindCSS                     │
└──────────────┬──────────────────────┘
               │ HTTP/REST
┌──────────────▼──────────────────────┐
│   BACKEND (API)                     │
│   - FastAPI Routers                 │
│   - Pydantic Models                 │
│   - Request/Response Handling       │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│   SERVICES (Lógica de Negocio)      │
│   - Business Logic                  │
│   - Validaciones                    │
│   - Transformaciones                │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│   DATABASE (Persistencia)           │
│   - SQLAlchemy ORM                  │
│   - SQLite                          │
│   - Connection Pooling              │
└─────────────────────────────────────┘
```

### 2.2 Principios de Diseño

- **Separación de Responsabilidades**: Cada capa tiene una responsabilidad única
- **DRY (Don't Repeat Yourself)**: Lógica reutilizable en servicios
- **Single Responsibility**: Cada módulo hace una cosa bien
- **Dependency Injection**: Servicios inyectados en rutas
- **RESTful API**: Endpoints REST estándar

---

## 🔧 3. BACKEND - FASTAPI

### 3.1 Aplicación Principal (`backend/api/main.py`)

**Características:**
- Framework: **FastAPI** (ASGI)
- Motor de templates: **Jinja2Templates**
- Servidor: **Uvicorn**
- Archivos estáticos: **StaticFiles**

**Configuración:**
```python
app = FastAPI(
    title="SGTE API",
    description="Sistema de Gestión de Titulaciones y Expedientes",
    version="2.0.0"
)
```

**Routers Incluidos:**
- `/api/estudiantes` → `estudiantes.router`
- `/api/proyectos` → `proyectos.router`
- `/api/documentos` → `documentos.router`
- `/api/expedientes` → `expedientes.router`
- `/api/operaciones` → `operaciones.router`
- `/api/reportes` → `reportes.router`
- `/api/dashboard` → `dashboard.router`

### 3.2 Rutas Frontend (Server-Side Rendering)

**Patrón:** FastAPI renderiza templates Jinja2 con datos del servidor

**Ejemplo:**
```python
@app.get("/estudiantes", response_class=HTMLResponse)
async def estudiantes_page(request: Request, q: str = None, ...):
    # Obtener datos mínimos del servidor (carreras, filtros)
    carreras = obtener_carreras()
    
    # NO pasar estudiantes - se cargan vía JavaScript
    return templates.TemplateResponse(
        "estudiantes/lista.html",
        {
            "request": request,
            "estudiantes": [],  # Vacío
            "carreras": carreras,
            "query": q or ""
        }
    )
```

**Rutas Frontend Principales:**
- `/` → `index.html`
- `/dashboard` → `dashboard.html`
- `/estudiantes` → `estudiantes/lista.html`
- `/estudiantes/nuevo` → `estudiantes/crear.html`
- `/estudiantes/{run}` → `estudiantes/detalle.html`
- `/estudiantes/{run}/editar` → `estudiantes/editar.html`
- `/proyectos` → `proyectos/lista.html`
- `/operaciones-masivas` → `operaciones/lista.html`
- `/documentos/{run}` → `documentos/detalle.html`

### 3.3 Estructura de Routers API

**Patrón de Router:**
```python
router = APIRouter(prefix="/api/estudiantes", tags=["estudiantes"])

@router.get("/")
async def listar_estudiantes(
    pagina: int = Query(1, ge=1),
    filas_por_pagina: int = Query(10, ge=1, le=100),
    termino: Optional[str] = None,
    carrera: Optional[str] = None
):
    # Lógica de negocio
    estudiantes = buscar_estudiantes(...)
    total = contar_estudiantes_filtrados(...)
    
    return {
        "success": True,
        "data": {
            "estudiantes": estudiantes,
            "paginacion": {
                "pagina_actual": pagina,
                "total_registros": total,
                "total_paginas": total_paginas
            }
        }
    }
```

**Endpoints Principales por Módulo:**

#### Estudiantes (`/api/estudiantes`)
- `GET /` - Listar con paginación
- `GET /{run}` - Obtener por RUN
- `POST /` - Crear
- `PUT /{run}` - Actualizar
- `DELETE /{run}` - Eliminar
- `GET /checklist-status` - Estado de checklist masivo
- `GET /carreras/lista` - Listar carreras

#### Proyectos (`/api/proyectos`)
- `GET /` - Listar con paginación
- `GET /{id}` - Obtener por ID
- `POST /` - Crear
- `PUT /{id}` - Actualizar
- `DELETE /{id}` - Eliminar

#### Operaciones (`/api/operaciones`)
- `POST /sincronizar-excel` - Sincronizar desde Excel
- `GET /estudiantes` - Listar estudiantes (paginado)
- `GET /carreras` - Listar carreras
- `POST /procesar-pdf` - Procesar PDF Splitter
- `GET /verificar-pdf-splitter` - Verificar disponibilidad

#### Documentos (`/api/documentos`)
- `GET /{run}` - Listar documentos de estudiante
- `POST /{run}/subir` - Subir documento
- `PUT /{id}/validar` - Validar documento
- `DELETE /{id}` - Eliminar documento

#### Expedientes (`/api/expedientes`)
- `GET /` - Listar expedientes
- `GET /{id}` - Obtener expediente
- `PUT /{id}` - Actualizar estado
- `GET /estadisticas` - Estadísticas

---

## 🎨 4. FRONTEND - JINJA2 + JAVASCRIPT

### 4.1 Template Base (`frontend/templates/base.html`)

**Características:**
- **Sidebar colapsable** (256px expandido / 80px colapsado)
- **Responsive** (móvil con overlay)
- **Navegación activa** (resaltado de ruta actual)
- **Persistencia de estado** (localStorage para sidebar)

**Estructura:**
```html
<!DOCTYPE html>
<html>
<head>
    <!-- TailwindCSS CDN -->
    <!-- Font Awesome -->
    <!-- Custom CSS -->
</head>
<body>
    <aside id="sidebar">      <!-- Sidebar fijo -->
    <div id="main-content">     <!-- Contenido principal -->
        <header>               <!-- Top bar -->
        <main>                 <!-- Contenido de página -->
            {% block content %}{% endblock %}
        </main>
    </div>
    <script src="/static/js/main.js"></script>
    {% block extra_scripts %}{% endblock %}
</body>
</html>
```

### 4.2 Sistema de Diseño

**Framework CSS:** TailwindCSS (CDN)
- Utilidades: `bg-teal-500`, `rounded-lg`, `shadow`, etc.
- Responsive: `md:grid-cols-4`, `lg:hidden`
- Estados: `hover:bg-teal-600`, `focus:ring-2`

**Colores Principales:**
- **Primario:** `#17A499` (teal-500)
- **Primario Oscuro:** `#0E7F76` (teal-700)
- **Primario Claro:** `#6FD1C8` (teal-300)
- **Fondo:** `bg-gray-50`
- **Texto:** `text-gray-800`

**Componentes Reutilizables:**
- Cards: `bg-white rounded-lg shadow p-6`
- Botones primarios: `bg-teal-500 hover:bg-teal-600 text-white px-6 py-3 rounded-lg`
- Inputs: `px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500`
- Tablas: `min-w-full divide-y divide-gray-200`

### 4.3 JavaScript - Patrón de Carga Dinámica

**Arquitectura Frontend:**
- **Server-Side Rendering (SSR)**: Templates Jinja2 renderizados en servidor
- **Client-Side Rendering (CSR)**: Datos cargados vía JavaScript (fetch API)
- **Híbrido**: Filtros y configuración desde servidor, datos desde API

**Helper API (`frontend/static/js/main.js`):**
```javascript
const api = {
    async get(url) {
        const response = await fetch(`/api${url}`);
        if (!response.ok) throw new Error(...);
        return await response.json();
    },
    async post(url, data) { ... },
    async put(url, data) { ... },
    async delete(url) { ... }
};
```

**Patrón de Paginación (Ejemplo: Estudiantes):**

```javascript
// Variables globales
var paginaActual = 1;
var filasPorPagina = 10;
var totalRegistros = 0;
var totalPaginas = 1;
var terminoBusqueda = '';
var carreraFiltro = '';
var modalidadFiltro = '';
var listoFiltro = null;

// Cargar datos
async function cargarEstudiantes() {
    const params = new URLSearchParams({
        pagina: paginaActual,
        filas_por_pagina: filasPorPagina,
        termino: terminoBusqueda || undefined,
        carrera: carreraFiltro || undefined,
        modalidad: modalidadFiltro || undefined,
        listo: listoFiltro !== null ? listoFiltro : undefined
    });
    
    const result = await api.get(`/estudiantes?${params}`);
    const { estudiantes, paginacion } = result.data;
    
    // Actualizar variables globales
    totalRegistros = paginacion.total_registros;
    totalPaginas = paginacion.total_paginas;
    
    // Renderizar tabla
    renderizarTabla(estudiantes);
    actualizarControlesPaginacion();
}

// Renderizar tabla HTML
function renderizarTabla(estudiantes) {
    const tbody = document.getElementById('tabla-estudiantes');
    tbody.innerHTML = estudiantes.map(est => `
        <tr>
            <td>${est.run}</td>
            <td>${est.nombre_completo}</td>
            <td>${est.carrera}</td>
            <td>${est.modalidad}</td>
            <td>...</td>
        </tr>
    `).join('');
}
```

### 4.4 Templates por Módulo

#### Estudiantes (`estudiantes/lista.html`)
- **Búsqueda:** Input de texto (RUN o nombre)
- **Filtros:** Carrera, Modalidad, Listo para apertura
- **Tabla:** RUN, Nombre, Carrera, Modalidad, Checklist, Acciones
- **Paginación:** 10/20/30/40 filas, navegación de páginas
- **Acciones:** Ver detalle, Editar, Checklist

#### Proyectos (`proyectos/lista.html`)
- **Búsqueda:** Término general
- **Filtros:** Carrera, Semestre
- **Tabla:** Título, RUN(s), Semestre, Modalidad, Profesor Guía
- **Paginación:** Misma que estudiantes

#### Operaciones Masivas (`operaciones/lista.html`)
- **Sincronización Excel:** Botón "🔄 Sincronizar Excel"
- **PDF Splitter:** Carga de PDF, procesamiento masivo
- **Lista de Estudiantes:** Con checkboxes para selección múltiple
- **Acciones Masivas:** Generar memorándums, exportar lista
- **Paginación:** 10/20/30/40 filas

---

## 💼 5. SERVICES - LÓGICA DE NEGOCIO

### 5.1 Estructura de Servicios

**Patrón:** Funciones puras que encapsulan lógica de negocio

**Ejemplo (`services/estudiantes.py`):**
```python
def crear_estudiante(
    run: str,
    nombres: str,
    apellidos: str,
    carrera: str,
    modalidad: str,
    usuario: str = None
) -> tuple[bool, str, Optional[Estudiante]]:
    """
    Crea un nuevo estudiante.
    
    Returns:
        (exito, mensaje, estudiante)
    """
    # 1. Validar RUN
    valido, msg = validar_run(run)
    if not valido:
        return False, msg, None
    
    # 2. Formatear RUN
    run_formateado = formatear_run(run)
    
    # 3. Verificar existencia
    with get_session_context() as session:
        existente = session.query(Estudiante).filter(...).first()
        if existente:
            return False, "Estudiante ya existe", None
        
        # 4. Crear
        estudiante = Estudiante(...)
        session.add(estudiante)
        
        # 5. Log en bitácora
        log_user_action(...)
        
        return True, "Estudiante creado", estudiante
```

### 5.2 Servicios Principales

#### `services/estudiantes.py`
- `validar_run()` - Validación de RUN chileno
- `formatear_run()` - Formato estándar XX.XXX.XXX-X
- `crear_estudiante()` - Crear nuevo estudiante
- `obtener_estudiante()` - Obtener por RUN
- `buscar_estudiantes()` - Búsqueda con filtros y paginación
- `actualizar_estudiante()` - Actualizar datos
- `eliminar_estudiante()` - Eliminar (soft delete)
- `obtener_carreras()` - Listar carreras únicas
- `contar_estudiantes_filtrados()` - Contar con filtros

#### `services/sync_excel.py`
- `sincronizar_excel()` - ETL Excel → SQLite
- `leer_excel()` - Leer múltiples hojas
- `procesar_fila()` - Procesar fila individual
- `limpiar_run()` - Limpiar y validar RUN
- `mapear_estado_excel()` - Mapear estados

#### `services/excel_export.py`
- `exportar_estudiantes()` - Exportar a Excel
- `exportar_proyectos()` - Exportar proyectos
- `obtener_datos_completos()` - Query completo con joins

#### `services/memo_generator.py`
- `generar_memorandum()` - Generar memorándum Word
- `generar_memorandums_masivos()` - Procesamiento masivo

#### `services/pdf_splitter_optimized.py`
- `procesar_pdf_masivo()` - Dividir PDF por RUNs
- `extraer_runs_ocr()` - OCR para extraer RUNs

---

## 🗄️ 6. DATABASE - SQLALCHEMY ORM

### 6.1 Modelos Principales

#### `Estudiante`
```python
class Estudiante(Base):
    __tablename__ = "estudiantes"
    
    run: Mapped[str] = mapped_column(String(12), primary_key=True)
    nombres: Mapped[str] = mapped_column(String(100))
    apellidos: Mapped[str] = mapped_column(String(100))
    carrera: Mapped[str] = mapped_column(String(100))
    modalidad: Mapped[str] = mapped_column(String(50))
    email: Mapped[Optional[str]] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, ...)
    
    # Relaciones
    proyectos_1: Mapped[List["Proyecto"]] = relationship(...)
    documentos: Mapped[List["Documento"]] = relationship(...)
```

#### `Proyecto`
```python
class Proyecto(Base):
    __tablename__ = "proyectos"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    estudiante_run1: Mapped[str] = mapped_column(String(12), ForeignKey("estudiantes.run"))
    estudiante_run2: Mapped[Optional[str]] = mapped_column(String(12), ForeignKey("estudiantes.run"))
    semestre: Mapped[str] = mapped_column(String(10))
    modalidad_titulacion: Mapped[str] = mapped_column(String(50))
    titulo: Mapped[Optional[str]] = mapped_column(String(500))
    link_documento: Mapped[Optional[str]] = mapped_column(String(500))
    
    # Relaciones
    estudiante_1: Mapped["Estudiante"] = relationship(...)
    comision: Mapped[Optional["Comision"]] = relationship(...)
    expediente: Mapped[Optional["Expediente"]] = relationship(...)
```

#### `Documento`
```python
class Documento(Base):
    __tablename__ = "documentos"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    estudiante_run: Mapped[str] = mapped_column(String(12), ForeignKey("estudiantes.run"))
    tipo: Mapped[TipoDocumento] = mapped_column(SQLEnum(TipoDocumento))
    path: Mapped[str] = mapped_column(String(500))
    validado: Mapped[bool] = mapped_column(Boolean, default=False)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
```

#### `Expediente`
```python
class Expediente(Base):
    __tablename__ = "expedientes"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    proyecto_id: Mapped[int] = mapped_column(Integer, ForeignKey("proyectos.id"), unique=True)
    estado: Mapped[EstadoExpediente] = mapped_column(SQLEnum(EstadoExpediente), default=EstadoExpediente.PENDIENTE)
    observaciones: Mapped[Optional[str]] = mapped_column(Text)
    fecha_envio: Mapped[Optional[datetime]] = mapped_column(DateTime)
    fecha_aprobacion: Mapped[Optional[datetime]] = mapped_column(DateTime)
    titulado: Mapped[bool] = mapped_column(Boolean, default=False)
```

### 6.2 Conexión a Base de Datos (`database/connection.py`)

**Características:**
- **SQLite** con modo WAL (Write-Ahead Logging)
- **Connection Pooling** (pool_size=1 para SQLite)
- **Retry Logic** con backoff exponencial
- **Context Manager** para sesiones

**Configuración SQLite:**
```python
# PRAGMAs optimizados
PRAGMA journal_mode=WAL          # Lecturas concurrentes
PRAGMA synchronous=NORMAL        # Balance velocidad/seguridad
PRAGMA cache_size=-131072        # 128MB cache
PRAGMA temp_store=MEMORY         # Tablas temporales en RAM
PRAGMA mmap_size=268435456       # 256MB memory-mapped I/O
PRAGMA foreign_keys=ON           # Foreign keys habilitadas
```

**Uso:**
```python
from database import get_session_context

with get_session_context() as session:
    estudiante = session.query(Estudiante).filter(...).first()
    # commit automático al salir del context
```

### 6.3 Enumeraciones (Enums)

```python
class EstadoExpediente(enum.Enum):
    PENDIENTE = "pendiente"           # 🔴
    EN_PROCESO = "en_proceso"         # 🟡
    LISTO_ENVIO = "listo_envio"       # 🟢
    ENVIADO = "enviado"               # 📤
    APROBADO = "aprobado"             # ✅
    TITULADO = "titulado"             # 🎓

class TipoDocumento(enum.Enum):
    BIENESTAR = "bienestar"
    FINANZAS_TITULO = "finanzas_titulo"
    FINANZAS_LICENCIA = "finanzas_licencia"
    BIBLIOTECA = "biblioteca"
    SDT = "sdt"
    MEMORANDUM = "memorandum"
    ACTA = "acta"
    OTRO = "otro"
```

---

## 🔄 7. FLUJO DE DATOS

### 7.1 Flujo de Carga de Página (Ejemplo: Estudiantes)

```
1. Usuario navega a /estudiantes
   ↓
2. FastAPI renderiza template Jinja2
   - Pasa: carreras, filtros iniciales
   - NO pasa: estudiantes (array vacío)
   ↓
3. Browser carga HTML + CSS + JavaScript
   ↓
4. JavaScript ejecuta al cargar página:
   - cargarEstudiantes() → fetch('/api/estudiantes?pagina=1&filas_por_pagina=10')
   ↓
5. Backend procesa request:
   - Router → Service → Database
   - Retorna: { estudiantes: [...], paginacion: {...} }
   ↓
6. JavaScript renderiza tabla:
   - renderizarTabla(estudiantes)
   - actualizarControlesPaginacion()
   ↓
7. Usuario interactúa:
   - Cambia página → cambiarPagina(n)
   - Cambia filas → cambiarFilasPorPagina(n)
   - Filtra → filtrarEstudiantes()
   - Cada acción → nueva llamada API → re-render
```

### 7.2 Flujo de Creación (Ejemplo: Crear Estudiante)

```
1. Usuario completa formulario en /estudiantes/nuevo
   ↓
2. JavaScript intercepta submit:
   - event.preventDefault()
   - Validación cliente
   - api.post('/estudiantes', datos)
   ↓
3. Backend procesa:
   - Router valida con Pydantic
   - Service valida RUN, verifica existencia
   - Database inserta
   - Log en bitácora
   ↓
4. Respuesta:
   - { success: true, data: {...} }
   ↓
5. JavaScript redirige:
   - window.location.href = '/estudiantes'
```

### 7.3 Flujo de Sincronización Excel

```
1. Usuario hace clic en "🔄 Sincronizar Excel"
   ↓
2. JavaScript:
   - api.post('/operaciones/sincronizar-excel')
   - Muestra loading
   ↓
3. Backend:
   - Lee Excel (pandas, múltiples hojas)
   - Por cada fila:
     a. Limpia RUN
     b. Busca estudiante existente
     c. Si existe → UPDATE
     d. Si no existe → INSERT
   - Retorna: { nuevos: X, actualizados: Y, errores: Z }
   ↓
4. JavaScript muestra resultado:
   - Toast/alert con resumen
   - Recarga lista de estudiantes
```

---

## 🎯 8. PATRONES DE DISEÑO IMPLEMENTADOS

### 8.1 Repository Pattern (Implícito)
- Servicios actúan como repositorios
- Abstraen acceso a base de datos

### 8.2 Service Layer Pattern
- Lógica de negocio separada de rutas
- Reutilizable entre diferentes interfaces

### 8.3 Context Manager Pattern
- `get_session_context()` para transacciones
- Commit/rollback automático

### 8.4 Singleton Pattern
- `Config` (config.py)
- `get_engine()` (cached)

### 8.5 Factory Pattern
- `SessionLocal` factory para sesiones

### 8.6 Strategy Pattern
- Diferentes estrategias de exportación (Excel, PDF)

---

## 📊 9. PAGINACIÓN - IMPLEMENTACIÓN

### 9.1 Backend

**Parámetros de Query:**
```python
@router.get("/")
async def listar_estudiantes(
    pagina: int = Query(1, ge=1),
    filas_por_pagina: int = Query(10, ge=1, le=100),
    termino: Optional[str] = None,
    carrera: Optional[str] = None
):
    offset = (pagina - 1) * filas_por_pagina
    
    # Aplicar filtros ANTES de paginar
    estudiantes = buscar_estudiantes(
        termino=termino,
        carrera=carrera,
        limite=filas_por_pagina,
        offset=offset
    )
    
    total = contar_estudiantes_filtrados(termino=termino, carrera=carrera)
    total_paginas = (total + filas_por_pagina - 1) // filas_por_pagina
    
    return {
        "success": True,
        "data": {
            "estudiantes": estudiantes,
            "paginacion": {
                "pagina_actual": pagina,
                "filas_por_pagina": filas_por_pagina,
                "total_registros": total,
                "total_paginas": total_paginas,
                "tiene_anterior": pagina > 1,
                "tiene_siguiente": pagina < total_paginas
            }
        }
    }
```

**SQL con LIMIT/OFFSET:**
```python
def buscar_estudiantes(..., limite: int = None, offset: int = None):
    query = session.query(Estudiante)
    
    # Aplicar filtros
    if termino:
        query = query.filter(or_(...))
    if carrera:
        query = query.filter(Estudiante.carrera == carrera)
    
    # Paginación en SQL (eficiente)
    if limite:
        query = query.limit(limite)
    if offset:
        query = query.offset(offset)
    
    return query.all()
```

### 9.2 Frontend

**Variables Globales:**
```javascript
var paginaActual = 1;
var filasPorPagina = 10;
var totalRegistros = 0;
var totalPaginas = 1;
```

**Controles de Paginación:**
```html
<select id="filas-por-pagina" onchange="cambiarFilasPorPagina()">
    <option value="10" selected>10</option>
    <option value="20">20</option>
    <option value="30">30</option>
    <option value="40">40</option>
</select>

<span id="info-paginacion">Mostrando 0 - 0 de 0</span>

<div id="navegacion-paginas">
    <!-- Botones generados dinámicamente -->
</div>
```

**Navegación:**
```javascript
function actualizarControlesPaginacion() {
    const inicio = (paginaActual - 1) * filasPorPagina + 1;
    const fin = Math.min(paginaActual * filasPorPagina, totalRegistros);
    
    document.getElementById('info-paginacion').textContent = 
        `Mostrando ${inicio} - ${fin} de ${totalRegistros}`;
    
    // Generar botones de páginas
    const nav = document.getElementById('navegacion-paginas');
    nav.innerHTML = generarBotonesPaginas();
}

function irAPagina(n) {
    paginaActual = n;
    cargarEstudiantes();
}
```

---

## 🎨 10. DISEÑO DE INTERFAZ

### 10.1 Sidebar

**Estados:**
- **Expandido:** 256px de ancho, texto visible
- **Colapsado:** 80px de ancho, solo iconos
- **Móvil:** Overlay, se oculta por defecto

**Persistencia:**
- Estado guardado en `localStorage`
- Se restaura al recargar página

**Navegación:**
- Resaltado de ruta activa (clase `active`)
- Iconos Font Awesome
- Hover effects

### 10.2 Tablas

**Estilo:**
- Headers: `bg-gray-50`
- Filas alternadas: `divide-y divide-gray-200`
- Hover: `hover:bg-gray-50`
- Responsive: `overflow-x-auto`

**Acciones:**
- Botones de acción en última columna
- Iconos Font Awesome
- Tooltips (opcional)

### 10.3 Formularios

**Inputs:**
- Border: `border-gray-300`
- Focus: `focus:ring-2 focus:ring-teal-500`
- Rounded: `rounded-lg`
- Padding: `px-4 py-2`

**Botones:**
- Primario: `bg-teal-500 hover:bg-teal-600`
- Secundario: `bg-gray-300 hover:bg-gray-400`
- Peligro: `bg-red-500 hover:bg-red-600`

### 10.4 Cards

**Estructura:**
- Fondo: `bg-white`
- Sombra: `shadow` o `shadow-lg`
- Rounded: `rounded-lg`
- Padding: `p-6`

---

## 🔐 11. SEGURIDAD Y VALIDACIÓN

### 11.1 Validación Backend

**Pydantic Models:**
```python
class EstudianteCreate(BaseModel):
    run: str
    nombres: str
    apellidos: str
    carrera: str
    modalidad: str
    email: Optional[str] = None
```

**Validación de RUN:**
- Formato: XX.XXX.XXX-X
- Dígito verificador chileno
- Validación matemática

### 11.2 SQL Injection

**Protección:**
- SQLAlchemy ORM (parametrizado)
- No se usa SQL crudo
- Filtros con `.filter()` seguro

### 11.3 XSS (Cross-Site Scripting)

**Protección:**
- Jinja2 escapa automáticamente: `{{ variable }}`
- JavaScript no inserta HTML crudo (usa `textContent` o sanitización)

---

## 📦 12. DEPENDENCIAS PRINCIPALES

### Backend
- `fastapi>=0.104.0` - Framework web
- `uvicorn[standard]>=0.24.0` - Servidor ASGI
- `sqlalchemy>=2.0.0` - ORM
- `pydantic>=2.5.0` - Validación de datos
- `jinja2>=3.1.0` - Templates
- `pandas>=2.0.0` - Manipulación de datos
- `openpyxl>=3.1.0` - Lectura/escritura Excel
- `python-docx>=1.0.0` - Generación Word
- `pymupdf>=1.23.0` - Procesamiento PDF
- `loguru>=0.7.0` - Logging

### Frontend (CDN)
- **TailwindCSS** - Framework CSS
- **Font Awesome 6.4.0** - Iconos

---

## 🚀 13. OPTIMIZACIONES IMPLEMENTADAS

### 13.1 Base de Datos
- **WAL Mode:** Lecturas concurrentes sin bloqueos
- **Cache Size:** 128MB en RAM
- **Memory-Mapped I/O:** 256MB
- **Connection Pooling:** Reutilización de conexiones

### 13.2 Frontend
- **Carga Dinámica:** Solo carga datos visibles (paginación)
- **Caché Local:** Variables globales para evitar re-fetch
- **Debounce:** En búsquedas (opcional)

### 13.3 Backend
- **Paginación SQL:** LIMIT/OFFSET en base de datos
- **Filtros en SQL:** No filtra en memoria
- **Lazy Loading:** SQLAlchemy relaciones lazy

---

## 📝 14. LOGGING Y MONITOREO

### 14.1 Loguru

**Configuración:**
```python
logger.add("logs/sgte_{time:YYYY-MM-DD}.log", 
           level="DEBUG", 
           rotation="1 day", 
           retention="30 days")
```

**Niveles:**
- `DEBUG` - Información detallada
- `INFO` - Operaciones normales
- `WARNING` - Advertencias
- `ERROR` - Errores
- `CRITICAL` - Errores críticos

### 14.2 Bitácora (Auditoría)

**Tabla `bitacora`:**
- Registra todas las acciones de usuario
- Campos: `tabla`, `registro_id`, `accion`, `usuario`, `timestamp`
- Usado para auditoría y trazabilidad

---

## 🎯 15. CONCLUSIONES

### Fortalezas
1. **Arquitectura clara:** Separación de responsabilidades
2. **Escalable:** Fácil agregar nuevos módulos
3. **Mantenible:** Código organizado y documentado
4. **Performante:** Paginación, caché, optimizaciones SQL
5. **Moderno:** FastAPI, SQLAlchemy 2.0, TailwindCSS

### Áreas de Mejora
1. **Autenticación:** No implementada (futuro)
2. **Tests:** No hay tests unitarios/integración
3. **Documentación API:** Swagger/OpenAPI básico
4. **Error Handling:** Mejorar mensajes de error al usuario
5. **Caché:** Implementar Redis para sesiones (futuro)

---

**Fin del Reporte**
