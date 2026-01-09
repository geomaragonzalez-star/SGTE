import sqlite3
from datetime import datetime

db_path = r'c:\Users\YomiT\Documents\Tesis\SGTE\data\sgte.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 1. Eliminar tablas existentes para recrearlas limpias
tables = ['estudiantes', 'proyectos', 'documentos', 'comisiones', 'expedientes', 'hitos', 'bitacora', 'app_logs']
for t in tables:
    cursor.execute(f"DROP TABLE IF EXISTS {t}")

# 2. Crear tabla ESTUDIANTES (Modificada)
cursor.execute('''
CREATE TABLE IF NOT EXISTS estudiantes (
    run VARCHAR(12) PRIMARY KEY,
    nombres VARCHAR(100) NOT NULL,
    apellidos VARCHAR(100) NOT NULL,
    carrera VARCHAR(150) NOT NULL,
    modalidad VARCHAR(20) NOT NULL,  -- Diurno, Vespertino, Online
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL
)
''')

# 3. Crear tabla PROYECTOS (Modificada)
cursor.execute('''
CREATE TABLE IF NOT EXISTS proyectos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    estudiante_run1 VARCHAR(12) NOT NULL,
    estudiante_run2 VARCHAR(12),
    semestre VARCHAR(10) NOT NULL,
    modalidad_titulacion VARCHAR(50) NOT NULL, -- Tesis, Capstone, etc.
    titulo VARCHAR(500),
    link_documento VARCHAR(500),
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    FOREIGN KEY (estudiante_run1) REFERENCES estudiantes (run),
    FOREIGN KEY (estudiante_run2) REFERENCES estudiantes (run)
)
''')

# 4. Recrear el resto de tablas (sin cambios mayores, asegurando integridad)
cursor.execute('''
CREATE TABLE IF NOT EXISTS documentos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    estudiante_run VARCHAR(12) NOT NULL,
    tipo VARCHAR(50) NOT NULL,
    path VARCHAR(500),
    validado BOOLEAN NOT NULL DEFAULT 0,
    uploaded_at DATETIME NOT NULL,
    validated_at DATETIME,
    validated_by VARCHAR(100),
    FOREIGN KEY (estudiante_run) REFERENCES estudiantes (run)
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS comisiones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    proyecto_id INTEGER NOT NULL,
    profesor_guia VARCHAR(150),
    corrector_1 VARCHAR(150),
    corrector_2 VARCHAR(150),
    FOREIGN KEY (proyecto_id) REFERENCES proyectos (id)
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS expedientes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    proyecto_id INTEGER NOT NULL,
    estado VARCHAR(20) NOT NULL,
    observaciones TEXT,
    fecha_envio DATETIME,
    fecha_aprobacion DATETIME,
    titulado BOOLEAN NOT NULL DEFAULT 0,
    semestre_titulacion VARCHAR(10),
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    FOREIGN KEY (proyecto_id) REFERENCES proyectos (id)
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS hitos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    proyecto_id INTEGER NOT NULL,
    tipo VARCHAR(50) NOT NULL,
    fecha DATETIME,
    completado BOOLEAN NOT NULL DEFAULT 0,
    observaciones TEXT,
    FOREIGN KEY (proyecto_id) REFERENCES proyectos (id)
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS bitacora (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tabla VARCHAR(50) NOT NULL,
    registro_id VARCHAR(50) NOT NULL,
    accion VARCHAR(50) NOT NULL,
    usuario VARCHAR(100),
    descripcion TEXT,
    valores_anteriores TEXT,
    valores_nuevos TEXT,
    timestamp DATETIME NOT NULL
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS app_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    level VARCHAR(20) NOT NULL,
    message TEXT NOT NULL,
    module VARCHAR(100),
    function VARCHAR(100),
    traceback TEXT,
    extra_data TEXT,
    timestamp DATETIME NOT NULL
)
''')

conn.commit()
conn.close()
print("Base de datos actualizada correctamente.")
