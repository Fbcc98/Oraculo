"""Punto de entrada y orquestador CLI del sistema Oráculo."""

import argparse
import json
import logging
import os
import sqlite3

from database.crear_db import DB_PATH, crear_base_datos
from etl.common import Common
from etl.loader import ORDEN_CARGA, Loader
from etl.match_processor import MatchProcessor
from etl.pipeline import Pipeline, PipelineError
from scrapers.artifact_store import auditar_archivo_ronda
from scrapers.match_crawler import normalizar_nombre_directorio, run_url_explorer
from scrapers.stats_scraper import procesar_archivo_ronda
from utils.json_reader import load_config, parsear_rondas_objetivo
from utils.logger import setup_logger
from utils.schema_explorer import elegir_carpeta, explorar_carpeta

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
URLS_DIR = os.path.join(RAW_DIR, "urls_league_rounds")
EVENTS_DIR = os.path.join(RAW_DIR, "league_events")
MATCH_STATS_DIR = os.path.join(RAW_DIR, "matchs_stats")
PLAYER_STATS_DIR = os.path.join(RAW_DIR, "players_stats")
MANAGERS_DIR = os.path.join(RAW_DIR, "managers")


# ---------------------------------------------------------------------------
# Utilidades de selección y puente Raw JSON -> ETL
# ---------------------------------------------------------------------------


def _listar_json(carpeta):
    if not os.path.isdir(carpeta):
        return []
    return sorted(f for f in os.listdir(carpeta) if f.endswith(".json"))


def _seleccionar_archivo(carpeta, etiqueta):
    archivos = _listar_json(carpeta)
    if not archivos:
        print(f"\nNo hay archivos JSON disponibles en {etiqueta}.")
        return None

    print(f"\nArchivos disponibles en {etiqueta}:")
    for idx, nombre in enumerate(archivos, start=1):
        print(f"  {idx}. {nombre}")
    print("  c. Cancelar y volver")

    seleccion = input(f"\nElige un archivo (1-{len(archivos)}): ").strip().lower()
    if seleccion == "c":
        return None

    try:
        return archivos[int(seleccion) - 1]
    except (ValueError, IndexError):
        print("\nSelección inválida.")
        return None


def _buscar_archivo_partido(carpeta, partido_id, ronda=None):
    """Localiza el JSON asociado a un partido priorizando la ronda exacta."""
    if not os.path.isdir(carpeta):
        return None

    sufijo_exacto = f"_R{ronda}_{partido_id}.json" if ronda is not None else None
    sufijo_general = f"_{partido_id}.json"

    candidatos = _listar_json(carpeta)
    if sufijo_exacto:
        for nombre in candidatos:
            if nombre.endswith(sufijo_exacto):
                return os.path.join(carpeta, nombre)

    for nombre in candidatos:
        if nombre.endswith(sufijo_general):
            return os.path.join(carpeta, nombre)

    return None


def _extraer_metadatos_competicion(eventos_json, nombre_archivo_eventos):
    """Extrae PAIS y LIGAS del primer evento con torneo en round_events."""
    eventos = (eventos_json or {}).get("events") or []
    if not isinstance(eventos, list):
        raise PipelineError(
            f"El archivo {nombre_archivo_eventos} debe contener una lista events."
        )
    primer_evento = next(
        (
            evento for evento in eventos
            if isinstance(evento, dict)
            and isinstance(evento.get("tournament"), dict)
            and evento["tournament"]
        ),
        None,
    )

    if not primer_evento:
        raise PipelineError(
            f"El archivo {nombre_archivo_eventos} no contiene eventos válidos."
        )

    torneo = primer_evento.get("tournament") or {}
    torneo_unico = torneo.get("uniqueTournament") or {}
    categoria = torneo.get("category") or {}
    temporada_info = primer_evento.get("season") or {}

    nombre_pais = categoria.get("name") or "Desconocido"
    id_pais = Common.entero(categoria.get("id"))
    if id_pais is None:
        id_pais = abs(hash(nombre_pais)) % 100000 + 1

    id_temporada = Common.entero(temporada_info.get("id"))
    if id_temporada is None:
        id_temporada = Common.entero(torneo_unico.get("id")) or 1

    nombre_liga = (
        torneo_unico.get("name") or torneo.get("name") or "Liga Desconocida"
    )
    temporada = str(temporada_info.get("year") or "N/A")

    pais = {
        "Id_pais": id_pais,
        "Nombre_pais": nombre_pais,
    }
    liga = {
        "Id_liga": id_temporada,
        "Id_pais": id_pais,
        "Nombre_liga": nombre_liga,
        "Id_temporada_externo": id_temporada,
        "Temporada": temporada,
    }
    return pais, liga


def _mapa_urls_ronda(nombre_archivo_eventos):
    """Carga el mapa {partido_id: url} si existe el archivo de URLs homólogo."""
    nombre_urls = nombre_archivo_eventos.replace("round_events_", "urls_", 1)
    ruta_urls = os.path.join(URLS_DIR, nombre_urls)
    if not os.path.exists(ruta_urls):
        return {}

    try:
        with open(ruta_urls, "r", encoding="utf-8") as f:
            datos = json.load(f)
        mapa = {}
        for url in datos.get("urls", []):
            if "#id:" in url:
                partido_id = Common.entero(url.split("#id:")[-1])
                if partido_id is not None:
                    mapa[partido_id] = url
        return mapa
    except (OSError, json.JSONDecodeError):
        return {}


def ejecutar_etl_desde_eventos(nombre_archivo_eventos, ronda_filtro=None):
    """Construye los casos de una jornada y los carga atómicamente en SQLite."""
    ruta_eventos = os.path.join(EVENTS_DIR, nombre_archivo_eventos)
    if not os.path.exists(ruta_eventos):
        logging.error(f"No existe el archivo de eventos: {ruta_eventos}")
        return

    with open(ruta_eventos, "r", encoding="utf-8") as f:
        eventos_json = json.load(f)

    if ronda_filtro is None and "_ronda_" in nombre_archivo_eventos:
        parte_ronda = nombre_archivo_eventos.split("_ronda_")[-1].replace(".json", "")
        ronda_filtro = Common.entero(parte_ronda)

    pais, liga = _extraer_metadatos_competicion(eventos_json, nombre_archivo_eventos)
    mapa_urls = _mapa_urls_ronda(nombre_archivo_eventos)

    match_processor = MatchProcessor()
    eventos_normalizados = match_processor.procesar_eventos_ronda(
        eventos_json,
        id_liga=liga["Id_liga"],
        ronda=ronda_filtro,
        urls=mapa_urls,
    )

    if not eventos_normalizados:
        logging.warning(
            f"No se encontraron partidos finalizados para la ronda {ronda_filtro} "
            f"en {nombre_archivo_eventos}."
        )
        return

    casos = []
    sin_estadisticas = 0

    for item in eventos_normalizados:
        partido = item["partido"]
        id_partido = partido["Id_partido"]
        ronda_partido = partido.get("Ronda") or ronda_filtro

        ruta_stats = _buscar_archivo_partido(
            MATCH_STATS_DIR, id_partido, ronda=ronda_partido
        )
        if not ruta_stats:
            logging.warning(
                f"Partido {id_partido} omitido: falta JSON en data/raw/matchs_stats/."
            )
            sin_estadisticas += 1
            continue

        ruta_lineups = _buscar_archivo_partido(
            PLAYER_STATS_DIR, id_partido, ronda=ronda_partido
        )
        ruta_managers = _buscar_archivo_partido(
            MANAGERS_DIR, id_partido, ronda=ronda_partido
        )

        equipos_con_pais = [
            {**eq, "Id_pais": pais["Id_pais"]} for eq in item["equipos"]
        ]

        contexto = {
            "paises": [pais],
            "liga": liga,
            "equipos": equipos_con_pais,
            "partido": partido,
            "partidos_equipos": item["partidos_equipos"],
            "id_equipo_local": item["id_equipo_local"],
            "id_equipo_visita": item["id_equipo_visita"],
        }

        casos.append(
            {
                "contexto": contexto,
                "match_json": ruta_stats,
                "player_json": ruta_lineups,
                "manager_json": ruta_managers,
            }
        )

    if not casos:
        logging.warning(
            "Ronda %s: %s partidos omitidos por falta de estadísticas. "
            "Ejecuta primero el Scraper (Etapa 2).",
            ronda_filtro,
            sin_estadisticas,
        )
        return

    pipeline = Pipeline(loader=Loader(db_path=DB_PATH, inicializar=True))
    resultado = pipeline.procesar_lote(casos, continuar_con_error=True)

    print("\n" + "-" * 50)
    print(f"RESUMEN DE CARGA ETL ({liga['Nombre_liga']} - Ronda {ronda_filtro})")
    print("-" * 50)
    print(f"  Partidos cargados en SQLite : {len(resultado['procesados'])}")
    print(f"  Partidos sin JSON de stats  : {sin_estadisticas}")
    print(f"  Partidos con error de carga : {len(resultado['errores'])}")

    for err in resultado["errores"]:
        pid = err["caso"]["contexto"]["partido"]["Id_partido"]
        logging.error(f"Error cargando partido {pid}: {err['error']}")


# ---------------------------------------------------------------------------
# Flujos principales de operación
# ---------------------------------------------------------------------------


def ejecutar_flujo_completo():
    """Descubre todas las rondas y ejecuta detalle y ETL por cada jornada."""
    config = load_config()
    rondas = parsear_rondas_objetivo(
        config["scraping_settings"].get("ronda_objetivo", 1)
    )

    print(f"\n[1/3] Descubriendo partidos y eventos (Rondas {rondas})...")
    run_url_explorer(rondas_override=rondas)
    pendientes = []

    for league in config.get("leagues", []):
        pais_slug = normalizar_nombre_directorio(league["country"])
        liga_slug = normalizar_nombre_directorio(league["name"])

        for season in league.get("seasons", []):
            temp_slug = normalizar_nombre_directorio(season["year"])
            for ronda in rondas:
                sufijo = f"{pais_slug}_{liga_slug}_{temp_slug}_ronda_{ronda}.json"
                archivo_urls = f"urls_{sufijo}"
                archivo_eventos = f"round_events_{sufijo}"
                print(f"\n[2/3] Descargando detalle: {league['name']}, ronda {ronda}...")
                if os.path.exists(os.path.join(URLS_DIR, archivo_urls)):
                    try:
                        resumen = procesar_archivo_ronda(archivo_urls)
                        pendientes.extend(
                            {**item, "archivo_urls": archivo_urls}
                            for item in resumen["incompletos"]
                        )
                    except (OSError, ValueError, KeyError) as error:
                        logging.error("No se pudo procesar %s: %s", archivo_urls, error)
                else:
                    logging.warning("No se generó %s; se omite descarga.", archivo_urls)

                print(f"\n[3/3] Cargando SQLite: {league['name']}, ronda {ronda}...")
                if os.path.exists(os.path.join(EVENTS_DIR, archivo_eventos)):
                    try:
                        ejecutar_etl_desde_eventos(archivo_eventos, ronda_filtro=ronda)
                    except (OSError, ValueError, sqlite3.Error) as error:
                        logging.error("ETL %s: %s", archivo_eventos, error)
                else:
                    logging.warning("No se encontró %s para carga ETL.", archivo_eventos)
    _reportar_pendientes(pendientes)
    return pendientes


def _reportar_pendientes(pendientes):
    logging.info("Resumen consolidado: %s partidos pendientes de scraping.", len(pendientes))
    for item in pendientes:
        logging.warning(
            "%s | partido %s | %s | faltantes: %s",
            item["archivo_urls"], item["partido_id"], item["url"],
            ", ".join(item["faltantes"]),
        )


def auditar_y_reintentar_pendientes(archivo_urls=None, ejecutar_reintento=True):
    """Audita uno o todos los índices; reintenta solo IDs finalizados incompletos.

    Retorna resúmenes posteriores al reintento, pendientes consolidados y errores
    de lectura separados. Un índice corrupto no detiene los demás archivos.
    """
    archivos = [os.fspath(archivo_urls)] if archivo_urls is not None else [
        nombre for nombre in _listar_json(URLS_DIR) if nombre.startswith("urls_")
    ]
    resultado = {"archivos": {}, "pendientes": [], "errores": []}
    for archivo in archivos:
        try:
            resumen = auditar_archivo_ronda(os.path.join(URLS_DIR, archivo), RAW_DIR)
            if ejecutar_reintento and resumen["incompletos"]:
                ids = [item["partido_id"] for item in resumen["incompletos"]]
                try:
                    procesar_archivo_ronda(archivo, solo_ids=ids)
                except (OSError, ValueError, KeyError) as error:
                    logging.error("Reintento %s: %s", archivo, error)
                    resultado["errores"].append({
                        "archivo_urls": archivo, "error": str(error),
                    })
                resumen = auditar_archivo_ronda(os.path.join(URLS_DIR, archivo), RAW_DIR)
            resultado["archivos"][archivo] = resumen
            resultado["pendientes"].extend(
                {**item, "archivo_urls": archivo} for item in resumen["incompletos"]
            )
        except (OSError, ValueError, KeyError) as error:
            logging.error("Auditoría %s: %s", archivo, error)
            resultado["errores"].append({"archivo_urls": archivo, "error": str(error)})
    _reportar_pendientes(resultado["pendientes"])
    if resultado["errores"]:
        logging.warning(
            "%s errores de auditoría/reintento.", len(resultado["errores"])
        )
    return resultado


def ver_estado_base_datos():
    """Muestra el conteo actual de registros en cada tabla de SQLite."""
    if not os.path.exists(DB_PATH):
        print(f"\nLa base de datos aún no existe en: {DB_PATH}")
        print("Usa la opción 'Inicializar / Verificar base de datos' para crearla.")
        return

    print("\n" + "=" * 45)
    print("  ESTADO ACTUAL DE SQLITE (oraculo.db)")
    print("=" * 45)
    with sqlite3.connect(DB_PATH) as conn:
        for tabla in ORDEN_CARGA:
            try:
                total = conn.execute(f'SELECT COUNT(*) FROM "{tabla}"').fetchone()[0]
                print(f"  {tabla:<25} : {total} registros")
            except sqlite3.Error:
                print(f"  {tabla:<25} : (tabla no creada)")
    print("=" * 45)


def menu_diagnostico():
    while True:
        print("\n" + "-" * 45)
        print("  DIAGNÓSTICO Y BASE DE DATOS")
        print("-" * 45)
        print("  1. Explorar esquemas de JSON crudos")
        print("  2. Ver conteo de registros en SQLite")
        print("  3. Inicializar / Verificar tablas de SQLite")
        print("  0. Volver al menú principal")
        print("-" * 45)

        sub = input("\nSelecciona una opción (0-3): ").strip()
        if sub == "1":
            carpeta = elegir_carpeta()
            explorar_carpeta(carpeta)
        elif sub == "2":
            ver_estado_base_datos()
        elif sub == "3":
            crear_base_datos(DB_PATH)
        elif sub == "0":
            break
        else:
            print("\nOpción no válida.")


def mostrar_menu_principal():
    print("\n" + "=" * 52)
    print("  ORÁCULO - ORQUESTADOR DE DATOS DEPORTIVOS")
    print("=" * 52)
    print("  1. Flujo Completo (Scraping + Carga a SQLite)")
    print("  2. Cargar datos descargados a SQLite (Solo ETL)")
    print("  3. Solo Scraping - Etapa 1: URLs y Eventos de Liga")
    print("  4. Solo Scraping - Etapa 2: Stats, Lineups y Managers")
    print("  5. Auditar / Reintentar partidos pendientes de Scraping")
    print("  6. Diagnóstico y Base de Datos (JSON / SQLite)")
    print("  0. Salir")
    print("=" * 52)


def ejecutar_menu_interactivo():
    while True:
        mostrar_menu_principal()
        opcion = input("\nSelecciona una opción (0-6): ").strip()

        if opcion == "1":
            ejecutar_flujo_completo()

        elif opcion == "2":
            archivo_eventos = _seleccionar_archivo(
                EVENTS_DIR, "data/raw/league_events"
            )
            if archivo_eventos:
                ejecutar_etl_desde_eventos(archivo_eventos)

        elif opcion == "3":
            print("\nIniciando Explorador de URLs y Eventos...")
            run_url_explorer()

        elif opcion == "4":
            archivo_urls = _seleccionar_archivo(
                URLS_DIR, "data/raw/urls_league_rounds"
            )
            if archivo_urls:
                procesar_archivo_ronda(archivo_urls)

        elif opcion == "5":
            auditar_y_reintentar_pendientes()

        elif opcion == "6":
            menu_diagnostico()

        elif opcion == "0":
            print("\nCerrando Oráculo. ¡Hasta pronto!\n")
            break

        else:
            print("\nOpción no válida. Selecciona un número del 0 al 6.")


def main():
    setup_logger()
    parser = argparse.ArgumentParser(
        description="Orquestador CLI para recolección y carga ETL de Oráculo."
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="Ejecuta el flujo completo (Scraping + ETL) para las rondas en config.json.",
    )
    parser.add_argument(
        "--etl",
        metavar="ARCHIVO_EVENTOS",
        nargs="?",
        const="__AUTO__",
        help="Ejecuta solo la carga ETL a SQLite (opcional: nombre del JSON en league_events).",
    )
    parser.add_argument(
        "--init-db",
        action="store_true",
        help="Inicializa o verifica el esquema de database/oraculo.db.",
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Muestra el conteo de registros por tabla en SQLite.",
    )
    parser.add_argument(
        "--retry-pending",
        metavar="ARCHIVO_URLS",
        nargs="?",
        const="__AUTO__",
        help="Audita y reintenta partidos incompletos de un índice URLs o de todos.",
    )
    args = parser.parse_args()

    if args.init_db:
        crear_base_datos(DB_PATH)
    elif args.status:
        ver_estado_base_datos()
    elif args.full:
        ejecutar_flujo_completo()
    elif args.retry_pending:
        auditar_y_reintentar_pendientes(
            None if args.retry_pending == "__AUTO__" else args.retry_pending
        )
    elif args.etl:
        if args.etl == "__AUTO__":
            archivos = _listar_json(EVENTS_DIR)
            if not archivos:
                print("\nNo hay archivos en data/raw/league_events/ para procesar.")
                return
            for archivo in archivos:
                ejecutar_etl_desde_eventos(archivo)
        else:
            ejecutar_etl_desde_eventos(args.etl)
    else:
        ejecutar_menu_interactivo()


if __name__ == "__main__":
    main()
