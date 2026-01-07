from datetime import datetime

MESES = {
    1: "enero", 2: "febrero", 3: "marzo", 4: "abril",
    5: "mayo", 6: "junio", 7: "julio", 8: "agosto",
    9: "septiembre", 10: "octubre", 11: "noviembre", 12: "diciembre"
}

def fecha_larga_es() -> str:
    """Retorna la fecha actual en formato largo en español"""
    hoy = datetime.now()
    return f"{hoy.day} de {MESES[hoy.month]} de {hoy.year}"
