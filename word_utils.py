"""Utilidades para manejo de documentos Word"""

import os
from datetime import datetime
import locale
import win32com.client
from pathlib import Path
from typing import Dict
import pythoncom

MESES = {
    1: "enero", 2: "febrero", 3: "marzo", 4: "abril",
    5: "mayo", 6: "junio", 7: "julio", 8: "agosto",
    9: "septiembre", 10: "octubre", 11: "noviembre", 12: "diciembre"
}

def fecha_larga_hoy() -> str:
    """Retorna la fecha actual en formato largo en español"""
    hoy = datetime.now()
    return f"{hoy.day} de {MESES[hoy.month]} de {hoy.year}"

class WordTemplate:
    """Clase para manejar plantillas Word y generar PDFs"""
    
    def __init__(self):
        # Inicializar COM en el hilo actual
        pythoncom.CoInitialize()
        self.word = win32com.client.Dispatch("Word.Application")
        self.word.Visible = False
        
    def generate_pdf(self, template_path: Path, output_path: Path, 
                    replacements: Dict[str, str]) -> None:
        """Genera un PDF usando bookmarks de Word"""
        # Abrir documento desde plantilla
        doc = self.word.Documents.Open(str(template_path))
        
        try:
            # Reemplazar valores en bookmarks
            for name, value in replacements.items():
                if doc.Bookmarks.Exists(name):
                    # Preservar el bookmark al escribir
                    rng = doc.Bookmarks(name).Range
                    rng.Text = value
                    doc.Bookmarks.Add(name, rng)
            
            # Guardar como PDF
            output_path.parent.mkdir(parents=True, exist_ok=True)
            doc.SaveAs(str(output_path), FileFormat=17)  # 17 = PDF
            
        finally:
            doc.Close(SaveChanges=False)
    
    def close(self):
        """Cierra Word y libera recursos"""
        if hasattr(self, 'word'):
            self.word.Quit()
            pythoncom.CoUninitialize()
