import pandas as pd
import sqlite3
from datetime import datetime
import os

# Configuración
excel_path = r'C:\Users\YomiT\Desktop\2024-1.xlsx'
db_path = r'c:\Users\YomiT\Documents\Tesis\SGTE\data\sgte.db'

print(f"Leemos archivo: {excel_path}")

try:
    df = pd.read_excel(excel_path)
    print("Columnas encontradas:", df.columns.tolist())
except Exception as e:
    print(f"Error leyendo Excel: {e}")
    exit()

# Conexión DB
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

registros_estudiantes = 0
registros_proyectos = 0
errores = []

# Mapeo basado en la posición de columnas que vimos (A, B, C, D, E)
# Ajustaremos nombres de columnas para normalizar
# Asumimos que la primera fila es encabezado.
# Renombramos columnas para facilitar acceso
df.columns = ['RUN', 'Nombres', 'Apellidos', 'Carrera', 'Modalidad'] + df.columns.tolist()[5:]

current_time = datetime.now()

for index, row in df.iterrows():
    try:
        # 1. Datos Estudiante
        run = str(row['RUN']).strip()
        if pd.isna(run) or run == 'nan':
            continue # Saltar filas vacías
            
        nombres = str(row['Nombres']).strip()
        apellidos = str(row['Apellidos']).strip()
        carrera = str(row['Carrera']).strip()
        
        # Modalidad Estudiante (Diurno/Vespertino/Online)
        modalidad_est = str(row['Modalidad']).strip()
        if pd.isna(modalidad_est) or modalidad_est == 'nan' or modalidad_est == '':
            modalidad_est = "Desconocido" # Valor por defecto si falta
            
        # Insertar Estudiante
        # Usamos INSERT OR REPLACE para actualizar si ya existe
        cursor.execute('''
            INSERT OR REPLACE INTO estudiantes (run, nombres, apellidos, carrera, modalidad, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (run, nombres, apellidos, carrera, modalidad_est, current_time, current_time))
        registros_estudiantes += 1

        # 2. Datos Proyecto
        # Asumimos semestre 2024-1 por el nombre del archivo
        semestre = "2024-1"
        
        # Intentamos buscar título si existe columna extra, sino None
        titulo = None
        if len(df.columns) > 5:
            posible_titulo = str(row[df.columns[5]]).strip()
            if not pd.isna(posible_titulo) and posible_titulo != 'nan':
                titulo = posible_titulo

        # Modalidad Titulación (Por defecto Tesis/Proyecto si no se especifica)
        modalidad_titulacion = "Trabajo de Titulación" 

        # Verificar si ya existe proyecto para este estudiante en este semestre
        cursor.execute('SELECT id FROM proyectos WHERE estudiante_run1 = ? AND semestre = ?', (run, semestre))
        existing_proj = cursor.fetchone()

        if not existing_proj:
            cursor.execute('''
                INSERT INTO proyectos (estudiante_run1, semestre, modalidad_titulacion, titulo, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (run, semestre, modalidad_titulacion, titulo, current_time, current_time))
            registros_proyectos += 1
        else:
            # Actualizar título si ahora lo tenemos y antes no
            if titulo:
                 cursor.execute('''
                    UPDATE proyectos SET titulo = ?, updated_at = ? WHERE id = ?
                ''', (titulo, current_time, existing_proj[0]))

    except Exception as e:
        errores.append(f"Error en fila {index+2} (RUN {run}): {e}")

conn.commit()
conn.close()

print(f"\n--- RESUMEN ---")
print(f"Estudiantes procesados: {registros_estudiantes}")
print(f"Proyectos creados: {registros_proyectos}")
if errores:
    print(f"\nErrores ({len(errores)}):")
    for err in errores[:5]:
        print(err)
    if len(errores) > 5: print("...")
