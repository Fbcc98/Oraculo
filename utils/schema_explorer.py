"""Explorador de esquemas para los JSON crudos almacenados en ``data/raw``.

Uso interactivo:
    python etl/schema_explorer.py

Uso directo:
    python etl/schema_explorer.py players_stats
    python etl/schema_explorer.py matchs_stats
    python etl/schema_explorer.py urls_league_rounds
"""

import argparse
import json
import os
from collections import defaultdict

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data", "raw")

DATA_DIRECTORIES = {
    "urls_league_rounds": {
        "label": "URLs de partidos por liga y ronda",
        "path": os.path.join(DATA_DIR, "urls_league_rounds"),
    },
    "matchs_stats": {
        "label": "Estadísticas agregadas por equipo",
        "path": os.path.join(DATA_DIR, "matchs_stats"),
    },
    "players_stats": {
        "label": "Alineaciones y estadísticas individuales",
        "path": os.path.join(DATA_DIR, "players_stats"),
    },
    "league_events": {
        "label": "Eventos generales por liga, temporada y ronda",
        "path": os.path.join(DATA_DIR, "league_events"),
    },
    "managers": {
        "label": "Managers local y visitante por partido",
        "path": os.path.join(DATA_DIR, "managers"),
    },
}

def cargar_jsons(ruta_carpeta):
    """Carga los JSON válidos de una carpeta y devuelve pares nombre/contenido."""
    documentos = []

    if not os.path.isdir(ruta_carpeta):
        print(f"La carpeta no existe: {ruta_carpeta}")
        return documentos

    for nombre_archivo in sorted(os.listdir(ruta_carpeta)):
        if not nombre_archivo.endswith(".json"):
            continue

        ruta_completa = os.path.join(ruta_carpeta, nombre_archivo)
        try:
            with open(ruta_completa, "r", encoding="utf-8") as archivo:
                documentos.append((nombre_archivo, json.load(archivo)))
        except (OSError, json.JSONDecodeError) as error:
            print(f"Error leyendo {nombre_archivo}: {error}")

    return documentos

def registrar_estructura(valor, ruta, campos):
    """Registra rutas de campos y los tipos encontrados en todos los JSON."""
    if isinstance(valor, dict):
        if not valor and ruta:
            campos[ruta].add("object vacío")

        for clave, valor_hijo in valor.items():
            ruta_hija = f"{ruta}.{clave}" if ruta else clave
            registrar_estructura(valor_hijo, ruta_hija, campos)
        return

    if isinstance(valor, list):
        if not valor:
            campos[ruta].add("lista vacía")
            return

        for elemento in valor:
            registrar_estructura(elemento, f"{ruta}[]", campos)
        return

    tipo = type(valor).__name__ if valor is not None else "null"
    campos[ruta].add(tipo)

def explorar_estructura_general(documentos):
    """Devuelve todos los caminos de campos encontrados en los documentos."""
    campos = defaultdict(set)

    for _, documento in documentos:
        registrar_estructura(documento, "", campos)

    return campos

def explorar_estadisticas_json(ruta_carpeta_jsons):
    """Compatibilidad con el explorador original de estadísticas de equipo."""
    grupos_unicos = set()
    estadisticas_unicas = set()

    for _, data in cargar_jsons(ruta_carpeta_jsons):
        for periodo in data.get("statistics", []):
            for grupo in periodo.get("groups", []):
                grupos_unicos.add(grupo.get("groupName", "Sin grupo"))

                for estadistica in grupo.get("statisticsItems", []):
                    key = estadistica.get("key")
                    name = estadistica.get("name")
                    estadisticas_unicas.add(f"Key: '{key}' -> Name: '{name}'")

    return grupos_unicos, estadisticas_unicas

def explorar_campos_lineups(documentos):
    """Extrae campos propios de jugadores, alineación y estadísticas individuales."""
    campos_jugador = set()
    campos_alineacion = set()
    campos_estadisticas = set()

    for _, data in documentos:
        for condicion in ("home", "away"):
            for registro in data.get(condicion, {}).get("players", []):
                campos_alineacion.update(
                    clave for clave in registro if clave not in {"player", "statistics"}
                )
                campos_jugador.update((registro.get("player") or {}).keys())
                campos_estadisticas.update((registro.get("statistics") or {}).keys())

    return campos_jugador, campos_alineacion, campos_estadisticas

def imprimir_lista(titulo, elementos):
    print(f"\n{titulo} ({len(elementos)}):")
    print("-" * 60)
    for elemento in sorted(elementos):
        print(f" - {elemento}")

def imprimir_estructura_general(campos):
    print(f"\nCAMPOS Y TIPOS ENCONTRADOS ({len(campos)}):")
    print("-" * 60)
    for ruta in sorted(campos):
        tipos = ", ".join(sorted(campos[ruta]))
        print(f" - {ruta}: {tipos}")

def explorar_carpeta(nombre_carpeta):
    """Muestra el esquema general y los campos específicos de la carpeta elegida."""
    configuracion = DATA_DIRECTORIES[nombre_carpeta]
    documentos = cargar_jsons(configuracion["path"])

    print("=" * 60)
    print(f"EXPLORADOR DE ESQUEMAS: {configuracion['label']}")
    print(f"Carpeta: {configuracion['path']}")
    print(f"JSON analizados: {len(documentos)}")
    print("=" * 60)

    if not documentos:
        print("No se encontraron JSON válidos para analizar.")
        return

    imprimir_estructura_general(explorar_estructura_general(documentos))

    if nombre_carpeta == "matchs_stats":
        grupos, estadisticas = explorar_estadisticas_json(configuracion["path"])
        imprimir_lista("GRUPOS DE ESTADÍSTICAS DE EQUIPO", grupos)
        imprimir_lista("KEYS DE ESTADÍSTICAS DE EQUIPO", estadisticas)

    elif nombre_carpeta == "players_stats":
        jugador, alineacion, estadisticas = explorar_campos_lineups(documentos)
        imprimir_lista("CAMPOS DEL OBJETO PLAYER", jugador)
        imprimir_lista("CAMPOS DE ALINEACIÓN", alineacion)
        imprimir_lista("KEYS DE ESTADÍSTICAS INDIVIDUALES", estadisticas)

def elegir_carpeta():
    """Muestra un menú para seleccionar una de las carpetas de data."""
    opciones = list(DATA_DIRECTORIES)

    print("\nCarpetas disponibles:")
    for indice, nombre in enumerate(opciones, start=1):
        print(f"  {indice}. {nombre} - {DATA_DIRECTORIES[nombre]['label']}")

    while True:
        seleccion = input(f"\nElige una carpeta (1-{len(opciones)}): ").strip()
        try:
            indice = int(seleccion) - 1
            return opciones[indice]
        except (ValueError, IndexError):
            print("Selección inválida. Intenta nuevamente.")


def main():
    parser = argparse.ArgumentParser(
        description="Explora los campos disponibles en los JSON de data."
    )
    parser.add_argument(
        "carpeta",
        nargs="?",
        choices=DATA_DIRECTORIES.keys(),
        help="Carpeta a analizar. Si se omite, se muestra un menú.",
    )
    args = parser.parse_args()

    nombre_carpeta = args.carpeta or elegir_carpeta()
    explorar_carpeta(nombre_carpeta)
