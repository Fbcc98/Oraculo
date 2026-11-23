"""Descubrimiento multironda a partir del JSON de eventos de Sofascore."""

import logging
from pathlib import Path

from scrapers.artifact_store import eventos_validos, guardar_json_atomico
from scrapers.browser_client import (
    BrowserClient, click_defensivo, esperar_capturas, fetch_json,
    registrar_captura, retirar_captura,
)
from utils.base import random_sleep
from utils.json_reader import load_config, parsear_rondas_objetivo


BASE_DIR = Path(__file__).resolve().parent.parent
data_dir = BASE_DIR / "data" / "raw" / "urls_league_rounds"
raw_league_events_dir = BASE_DIR / "data" / "raw" / "league_events"


def normalizar_nombre_directorio(valor):
    """Normaliza nombres usados en la jerarquía de datos crudos."""
    return str(valor).strip().lower().replace(" ", "-").replace("/", "-")
1


def construir_urls_eventos(datos):
    """Construye URLs canónicas desde events, deduplicadas por ID de partido."""
    if not eventos_validos(datos):
        raise ValueError("La respuesta de la ronda debe contener una lista events.")
    urls, vistos = [], set()
    for evento in datos["events"]:
        if not isinstance(evento, dict):
            logging.warning("Evento inválido en la ronda: %r", evento)
            continue
        pid, slug, custom_id = (evento.get(k) for k in ("id", "slug", "customId"))
        if (
            type(pid) is not int or pid < 1
            or not isinstance(slug, str) or not slug.strip()
            or not isinstance(custom_id, str) or not custom_id.strip()
        ):
            logging.warning(
                "Evento %s sin id, slug o customId válido; se omite URL.", pid
            )
            continue
        if pid not in vistos:
            vistos.add(pid)
            urls.append(
                f"https://www.sofascore.com/football/match/{slug}/{custom_id}#id:{pid}"
            )
    return urls


def _seleccionar_ronda(page, ronda):
    opcion = page.get_by_role("option", name=f"Round {ronda}", exact=True)
    if not opcion.is_visible():
        click_defensivo(
            page, page.get_by_role("combobox", name="Select item in event list")
        )
    click_defensivo(page, opcion)


def run_url_explorer(rondas_override=None):
    """Visita cada temporada una vez por sesión y persiste eventos y URLs por ronda."""
    config = load_config()
    settings = config["scraping_settings"]
    rondas = parsear_rondas_objetivo(
        settings.get("ronda_objetivo", 1)
        if rondas_override is None else rondas_override
    )
    with BrowserClient(settings.get("browser_recycle_rounds", 5)) as cliente:
        for league in config["leagues"]:
            pais = normalizar_nombre_directorio(league["country"])
            liga = normalizar_nombre_directorio(league["name"])
            tournament_id = league["tournament_id"]
            for season in league["seasons"]:
                temp = normalizar_nombre_directorio(season["year"])
                season_id = season["season_id"]
                url_base = (
                    f"https://www.sofascore.com/tournament/football/"
                    f"{pais}/{liga}/{tournament_id}#id:{season_id}"
                )
                cargar_base = True
                for ronda in rondas:
                    page = listener = None
                    endpoint = (
                        f"/api/v1/unique-tournament/{tournament_id}"
                        f"/season/{season_id}/events/round/{ronda}"
                    )
                    try:
                        page, nueva = cliente.get_page()
                        capturas, listener = registrar_captura(
                            page, {"events": (endpoint, eventos_validos)}
                        )
                        if cargar_base or nueva:
                            cargar_base = True
                            page.goto(
                                url_base, wait_until="domcontentloaded", timeout=60000
                            )
                            cargar_base = False
                            random_sleep(
                                settings["delay_min_seconds"],
                                settings["delay_max_seconds"],
                            )
                        try:
                            _seleccionar_ronda(page, ronda)
                        except Exception as error:
                            logging.warning(
                                "Ronda %s: selector no disponible: %s", ronda, error
                            )
                        esperar_capturas(page, capturas, ["events"])
                        datos = capturas.get("events")
                        if datos is None:
                            datos = fetch_json(page, endpoint)
                        if not eventos_validos(datos):
                            raise ValueError("La respuesta requiere una lista 'events'.")
                        sufijo = f"{pais}_{liga}_{temp}_ronda_{ronda}.json"
                        guardar_json_atomico(
                            datos,
                            Path(raw_league_events_dir) / f"round_events_{sufijo}",
                        )
                        urls = construir_urls_eventos(datos)
                        guardar_json_atomico({
                            "liga": league["name"], "pais": pais,
                            "temporada": season["year"], "ronda": ronda, "urls": urls,
                        }, Path(data_dir) / f"urls_{sufijo}")
                        logging.info(
                            "%s %s ronda %s: %s URLs guardadas.",
                            liga, temp, ronda, len(urls),
                        )
                    except Exception as error:
                        logging.error("%s %s ronda %s: %s", liga, temp, ronda, error)
                    finally:
                        if listener is not None:
                            retirar_captura(page, listener)
                        cliente.finish_unit()
                    random_sleep(
                        settings["delay_min_seconds"], settings["delay_max_seconds"]
                    )
