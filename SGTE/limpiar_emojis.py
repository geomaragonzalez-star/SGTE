"""
Script para eliminar emojis de archivos Python de Streamlit
"""
import re
from pathlib import Path

# Archivos a procesar
archivos = [
    'pages/2_Estudiantes.py',
    'pages/3_Documentos.py',
    'pages/4_Operaciones_Masivas.py',
    'pages/5_Reportes.py',
    'pages/6_PDF_Splitter.py'
]

# Patrones de emojis comunes
emoji_pattern = re.compile(r'[📋👤📄⚡📊📚🎓✅❌🔍⚙️💾ℹ️➕🔄📈📉📌🆕🚦🔴🟡🟢📤📥💡🎯🔧📝📑🗂️📊📈📉]+\s*')

for archivo in archivos:
    filepath = Path(archivo)
    if not filepath.exists():
        print(f"❌ No existe: {archivo}")
        continue
    
    print(f"Procesando: {archivo}")
    
    # Leer contenido
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Reemplazos
    original_content = content
    
    # 1. Comentarios de encabezado
    content = re.sub(r'# pages/\d+_[📋👤📄⚡📊📚]+_', '# pages/', content)
    
    # 2. page_icon en set_page_config
    content = re.sub(r'page_icon="[📋👤📄⚡📊📚🎓]+"', 'page_icon="📊"', content)
    
    # 3. st.title, st.header, st.subheader
    content = emoji_pattern.sub('', content)
    
    # 4. Referencias a archivos de páginas en switch_page
    content = re.sub(r'pages/\d+_[📋👤📄⚡📊📚]+_', 'pages/', content)
    
    # Guardar si hubo cambios
    if content != original_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ Actualizado: {archivo}")
    else:
        print(f"ℹ️  Sin cambios: {archivo}")

print("\n✅ Proceso completado")
