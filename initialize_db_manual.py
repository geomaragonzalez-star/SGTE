import sys
import os

# Agregar directorio actual al path
sys.path.append(os.getcwd())

from database.connection import init_database
from loguru import logger

if __name__ == "__main__":
    logger.info("Inicializando base de datos manualmente...")
    if init_database():
        logger.info("✅ Base de datos inicializada correctamente")
    else:
        logger.error("❌ Falló la inicialización")
