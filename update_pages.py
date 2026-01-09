
import os
from pathlib import Path

pages_dir = Path("pages")

for file_path in pages_dir.glob("*.py"):
    print(f"Procesando: {file_path}")
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # 1. Añadir importación
    if "from services.ui import" in content:
        content = content.replace(
            "from services.ui import inject_custom_css",
            "from services.ui import inject_custom_css, render_global_sidebar"
        )
        content = content.replace(
            "from services.ui import inject_custom_css, render_hero, render_metric_card",
            "from services.ui import inject_custom_css, render_hero, render_metric_card, render_global_sidebar"
        )
    
    # 2. Reemplazar llamada a inject_custom_css con la llamada al sidebar también
    # Buscamos 'inject_custom_css()' y añadimos la llamada al sidebar justo después
    if "inject_custom_css()" in content:
        page_name = file_path.stem.split("_", 1)[1] if "_" in file_path.stem else file_path.stem
        # Mapeo manual de nombres para coincidir con el sidebar
        name_map = {
            "Dashboard": "Dashboard",
            "Estudiantes": "Estudiantes",
            "Documentos": "Documentos",
            "Operaciones_Masivas": "Operaciones Masivas",
            "Reportes": "Reportes",
            "PDF_Splitter": "PDF Splitter"
        }
        page_label = name_map.get(page_name, page_name)
        
        replacement = f"""inject_custom_css()
    
# Renderizar Sidebar Global
render_global_sidebar(current_page="{page_label}")"""
        
        content = content.replace("inject_custom_css()", replacement)
    
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

print("✅ Todas las páginas actualizadas.")
