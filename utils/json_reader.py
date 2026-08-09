import json
import os

def load_config():
    """Busca y carga el archivo config.json desde la raíz del proyecto."""
    # Sube dos niveles: desde utils/ -> a la raíz del proyecto
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(base_dir, 'config.json')

    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)