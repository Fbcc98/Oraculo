"""Extracción granular e idempotente de estadísticas, alineaciones y managers."""

import logging
from pathlib import Path

from scrapers.artifact_store import (
    archivo_valido, artefacto_valido, guardar_json_atomico, inspeccionar_ronda,
    pendiente, reportar_resumen, resumen_ronda,
)
from scrapers.browser_client import (
    BrowserClient, click_defensivo, esperar_capturas, fetch_json,
    registrar_captura, retirar_captura,
)
from utils.base import random_sleep
from utils.json_reader import load_config


BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"
INPUT_FOLDER = RAW_DIR / "urls_league_rounds"
RECURSOS = {"stats": "statistics", "lineups": "lineups", "managers": "managers"}


def _activar_pestanas(page, faltantes):
    selectores = []
    if "lineups" in faltantes or "managers" in faltantes:
        selectores.extend([
            'button[data-testid="tab-2"]', 'button[data-testid="tab-1"]',
        ])
    if "stats" in faltantes:
        selectores.append('button[data-testid="tab-statistics"]')
    for selector in selectores:
        try:
            click_defensivo(page, page.locator(selector))
        except Exception as error:
            logging.debug("Pestaña %s no disponible: %s", selector, error)


def _descargar_faltantes(page, partido):
    """Instala todos los listeners necesarios antes de navegar al partido."""
    pid = partido["partido_id"]
    recursos = {
        tipo: (
            f"/api/v1/event/{pid}/{RECURSOS[tipo]}",
            lambda datos, tipo=tipo: artefacto_valido(datos, tipo),
        )
        for tipo in partido["faltantes"]
    }
    capturas, listener = registrar_captura(page, recursos)
    guardados = 0
    try:
        try:
            page.goto(partido["url"], wait_until="domcontentloaded", timeout=30000)
        except Exception as error:
            # Un timeout de navegación no invalida respuestas ya recibidas.
            logging.warning("Partido %s: navegación parcial: %s", pid, error)
        try:
            _activar_pestanas(page, [tipo for tipo in recursos if tipo not in capturas])
            esperar_capturas(page, capturas, recursos)
        except Exception as error:
            logging.warning(
                "Partido %s: carga de pestañas interrumpida: %s", pid, error
            )
        for tipo, (endpoint, validar) in recursos.items():
            try:
                datos = capturas.get(tipo)
                if datos is None:
                    datos = fetch_json(page, endpoint)
                if not validar(datos):
                    raise ValueError(f"Respuesta vacía o inválida para {tipo}.")
                guardar_json_atomico(datos, partido["rutas"][tipo])
                guardados += 1
                logging.info("Partido %s: guardado %s.", pid, tipo)
            except Exception as error:
                logging.warning(
                    "Partido %s: no se pudo guardar %s: %s", pid, tipo, error
                )
    finally:
        retirar_captura(page, listener)
    return guardados


def procesar_archivo_ronda(nombre_archivo_json, solo_ids=None):
    """Procesa solo finalizados y retorna un resumen con faltantes reintentables.

    No abre Chromium si todos los archivos son válidos o no hay encuentros
    elegibles. Un homólogo de eventos corrupto aborta antes de navegar.
    """
    settings = load_config()["scraping_settings"]
    partidos = inspeccionar_ronda(
        Path(INPUT_FOLDER) / nombre_archivo_json, RAW_DIR, solo_ids
    )
    resumen = resumen_ronda(partidos)
    resumen["incompletos"] = []
    cola = [p for p in partidos if p["finalizado"] and p["faltantes"]]
    fallos_consecutivos = 0
    umbral = settings.get("circuit_breaker_threshold", 3)
    if type(umbral) is not int or umbral < 3:
        raise ValueError("circuit_breaker_threshold debe ser un entero >= 3.")

    with BrowserClient(settings.get("browser_recycle_matches", 50)) as cliente:
        for indice, partido in enumerate(cola):
            guardados = 0
            try:
                page, _ = cliente.get_page()
                guardados = _descargar_faltantes(page, partido)
            except Exception as error:
                logging.error("Partido %s: %s", partido["partido_id"], error)
            finally:
                cliente.finish_unit()
            partido["faltantes"] = [
                tipo for tipo, ruta in partido["rutas"].items()
                if not archivo_valido(ruta, tipo)
            ]
            if partido["faltantes"]:
                resumen["incompletos"].append(pendiente(partido))
            else:
                resumen["completos"] += 1
            fallos_consecutivos = fallos_consecutivos + 1 if guardados == 0 else 0
            if fallos_consecutivos >= umbral:
                logging.warning(
                    "Circuit breaker: %s partidos sin descargas; enfriando.",
                    fallos_consecutivos,
                )
                cliente.recycle()
                random_sleep(
                    settings.get("cooldown_min_seconds", 60),
                    settings.get("cooldown_max_seconds", 90),
                )
                fallos_consecutivos = 0
            elif indice + 1 < len(cola):
                random_sleep(settings["delay_min_match"], settings["delay_max_match"])

    for partido in partidos:
        if partido["finalizado"] and not partido["faltantes"] and partido not in cola:
            logging.info(
                "Partido %s omitido: los tres JSON son válidos.", partido["partido_id"]
            )
    reportar_resumen(resumen, str(nombre_archivo_json))
    return resumen
