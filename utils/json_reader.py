import json
import os
import re


def load_config(config_path=None):
    """Carga la ruta indicada o config.json desde la raíz del proyecto."""
    # Sube dos niveles: desde utils/ -> a la raíz del proyecto
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if config_path is None:
        config_path = os.path.join(base_dir, 'config.json')

    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def parsear_rondas_objetivo(valor):
    """Resuelve enteros, listas, rangos inclusivos o listas CSV de rondas.

    Rechaza booleanos, listas vacías, valores no positivos y rangos inversos.
    Conserva el orden y elimina duplicados para no repetir una descarga.
    """
    if type(valor) is int:
        rondas = [valor]
    elif isinstance(valor, list):
        rondas = valor
    elif isinstance(valor, str):
        valor = valor.strip()
        rango = re.fullmatch(r"([0-9]+)\s*-\s*([0-9]+)", valor)
        if rango:
            inicio, fin = map(int, rango.groups())
            if inicio < 1 or fin < inicio:
                raise ValueError("El rango debe ser positivo y ascendente.")
            rondas = list(range(inicio, fin + 1))
        elif re.fullmatch(r"[0-9]+(?:\s*,\s*[0-9]+)*", valor):
            rondas = [int(item.strip()) for item in valor.split(",")]
        else:
            raise ValueError(f"Formato de rondas inválido: {valor!r}")
    else:
        raise ValueError("Las rondas deben ser un entero, una lista o una cadena.")

    if not rondas or any(type(ronda) is not int or ronda < 1 for ronda in rondas):
        raise ValueError("Todas las rondas deben ser enteros positivos.")
    return list(dict.fromkeys(rondas))
