import logging
import os
import sys

def setup_logger():
    """
    Configura y inicializa el logger centralizado para todo el framework.
    Escribe los logs tanto en la consola como en un archivo en la raíz del proyecto.
    """
    # 1. Determinamos la raíz del proyecto (un nivel arriba de la carpeta 'utils')
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    log_file_path = os.path.join(base_dir, "oraculo_scraper.log")

    # 2. Evitamos configurar el logger múltiples veces si ya está configurado
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(
            level=logging.INFO, # Nivel mínimo a capturar
            format='%(asctime)s [%(levelname)s] %(message)s', # Formato visual
            datefmt='%Y-%m-%d %H:%M:%S',
            handlers=[
                logging.FileHandler(log_file_path, encoding='utf-8'), # Salida a archivo
                logging.StreamHandler(sys.stdout) # Salida a consola
            ]
        )