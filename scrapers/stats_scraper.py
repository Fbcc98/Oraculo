import json
import logging
import os
import sys

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(base_dir)

from utils.base import random_sleep
from utils.json_reader import load_config
from utils.logger import setup_logger

setup_logger()

INPUT_FOLDER = os.path.join(base_dir, "data", 'raw', "urls_league_rounds")
OUTPUT_FOLDER = os.path.join(base_dir, "data", 'raw', "matchs_stats")
PLAYER_STATS_FOLDER = os.path.join(base_dir, "data", 'raw', "players_stats")
MANAGERS_FOLDER = os.path.join(base_dir, "data", "raw", "managers")

os.makedirs(OUTPUT_FOLDER, exist_ok=True)
os.makedirs(PLAYER_STATS_FOLDER, exist_ok=True)
os.makedirs(MANAGERS_FOLDER, exist_ok=True)

LINEUPS_TAB_LOCATOR = 'button[data-testid="tab-1"]'

PLAYER_STATS_TAB_LOCATOR = 'button[data-testid="tab-2"]'

LINEUPS_ENDPOINT_TEMPLATE = (
    "https://www.sofascore.com/api/v1/event/{partido_id}/lineups"
)
MANAGERS_ENDPOINT_TEMPLATE = (
    "https://www.sofascore.com/api/v1/event/{partido_id}/managers"
)


def guardar_json(datos, carpeta_salida, nombre_archivo):
    """Guarda una respuesta JSON cruda conservando caracteres Unicode."""
    ruta_salida = os.path.join(carpeta_salida, nombre_archivo)

    with open(ruta_salida, "w", encoding="utf-8") as archivo:
        json.dump(datos, archivo, indent=4, ensure_ascii=False)

    return ruta_salida


def es_respuesta_lineups(response, partido_id):
    """Identifica la respuesta de alineaciones del partido actual."""
    ruta_esperada = f"/api/v1/event/{partido_id}/lineups"
    return ruta_esperada in response.url and response.status == 200


def es_respuesta_managers(response, partido_id):
    """Identifica la respuesta de managers del partido actual."""
    ruta_esperada = f"/api/v1/event/{partido_id}/managers"
    return ruta_esperada in response.url and response.status == 200


def obtener_lineups_desde_endpoint(page, partido_id, timeout=15000):
    """Obtiene lineups directamente usando la sesión abierta del navegador."""
    endpoint = LINEUPS_ENDPOINT_TEMPLATE.format(partido_id=partido_id)
    response = page.request.get(endpoint, timeout=timeout)

    if not response.ok:
        raise RuntimeError(
            f"El endpoint de alineaciones respondió HTTP {response.status}: {endpoint}"
        )

    return response.json()


def obtener_managers_desde_endpoint(page, partido_id, timeout=15000):
    """Obtiene managers directamente usando la sesión abierta del navegador."""
    endpoint = MANAGERS_ENDPOINT_TEMPLATE.format(partido_id=partido_id)
    response = page.request.get(endpoint, timeout=timeout)

    if not response.ok:
        raise RuntimeError(
            f"El endpoint de managers respondió HTTP {response.status}: {endpoint}"
        )

    datos = response.json()
    if not isinstance(datos, dict) or not (
        "homeManager" in datos or "awayManager" in datos
    ):
        raise ValueError(
            "La respuesta de managers no contiene 'homeManager' ni 'awayManager'."
        )

    return datos

def obtener_lineups(page, partido_id, timeout=15000):
    """
    Obtiene el JSON de alineaciones y estadísticas individuales.

    Fuerza la navegación a la pestaña de Estadísticas del Jugador y luego
    vuelve a Alineaciones para interceptar limpiamente la respuesta de red.
    """

    btn_player_stats = page.locator(PLAYER_STATS_TAB_LOCATOR)
    btn_lineups = page.locator(LINEUPS_TAB_LOCATOR)

    try:
        logging.info("Forzando recarga: Navegando a 'Estadísticas del Jugador'...")

        btn_player_stats.click(timeout=timeout)

        page.wait_for_timeout(1500)

        logging.info("Volviendo a 'Alineaciones' e interceptando el JSON...")

        with page.expect_response(
                lambda response: es_respuesta_lineups(response, partido_id), timeout=timeout,
        ) as response_info:

            btn_lineups.click(timeout=timeout)

        logging.info("¡Bingo! JSON de lineups interceptado con éxito.")
        return response_info.value.json()

    except PlaywrightTimeoutError:
        logging.warning(
            "PlaywrightTimeoutError: La pestaña no generó la respuesta 'lineups' a tiempo; se usará el endpoint."
        )
    except Exception as error:
        logging.warning(
            f"No fue posible capturar lineups desde la interfaz: {error}. "
            "Se usará el endpoint."
        )

    return obtener_lineups_desde_endpoint(page, partido_id, timeout=timeout)


def obtener_lineups_y_managers(page, partido_id, timeout=15000):
    """Obtiene lineups e intenta capturar managers durante el clic de Lineups."""
    respuestas_managers = []

    def registrar_managers(response):
        if es_respuesta_managers(response, partido_id):
            respuestas_managers.append(response)

    page.on("response", registrar_managers)
    try:
        lineups = obtener_lineups(page, partido_id, timeout=timeout)
        page.wait_for_timeout(500)
    finally:
        page.remove_listener("response", registrar_managers)

    managers = None
    if respuestas_managers:
        try:
            managers = respuestas_managers[-1].json()
            logging.info("JSON de managers interceptado durante el clic en Lineups.")
        except Exception as error:
            logging.warning(
                f"La respuesta interceptada de managers no pudo leerse: {error}"
            )

    if managers is None:
        logging.info(
            "No se interceptó managers durante el clic; consultando el endpoint."
        )
        try:
            managers = obtener_managers_desde_endpoint(
                page,
                partido_id,
                timeout=timeout,
            )
        except Exception as error:
            logging.error(
                f"No se pudo obtener managers para el partido {partido_id}: {error}"
            )

    return lineups, managers

def obtener_estadisticas_equipo(page, partido_id, timeout=15000):
    """Abre la pestaña de estadísticas e intercepta el JSON del partido."""
    logging.info("Buscando la pestaña de Estadísticas...")
    btn_stats = page.locator('button[data-testid="tab-statistics"]')

    if not btn_stats.is_visible():
        raise RuntimeError("No se ve la pestaña de Estadísticas.")

    logging.info("Pestaña de Estadísticas encontrada. Interceptando respuesta...")
    ruta_esperada = f"/api/v1/event/{partido_id}/statistics"

    with page.expect_response(
        lambda response: ruta_esperada in response.url and response.status == 200,
        timeout=timeout,
    ) as response_info:
        btn_stats.click()

    return response_info.value.json()


def procesar_archivo_ronda(nombre_archivo_json):
    config = load_config()
    settings = config["scraping_settings"]

    ruta_input = os.path.join(INPUT_FOLDER, nombre_archivo_json)

    if not os.path.exists(ruta_input):
        logging.error(f"El archivo {ruta_input} no existe.")
        return

    with open(ruta_input, "r", encoding="utf-8") as archivo:
        datos_ronda = json.load(archivo)

    urls_partidos = datos_ronda.get("urls", [])
    liga = datos_ronda.get("liga", "Desconocida")
    ronda = datos_ronda.get("ronda", 0)

    logging.info(f"Iniciando extracción para {liga} - Ronda {ronda}")
    logging.info(f"Total de partidos a procesar: {len(urls_partidos)}")

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=False,
            args=["--start-maximized"],
        )
        context = browser.new_context(
            user_agent=settings["user_agent_default"],
            no_viewport=True,
        )
        page = context.new_page()

        lineups_guardados = 0
        managers_guardados = 0
        estadisticas_guardadas = 0

        for indice, url in enumerate(urls_partidos, start=1):
            logging.info("---")
            logging.info(f"Procesando partido {indice}/{len(urls_partidos)}")
            logging.info(f"URL: {url}")

            partido_id = (
                url.split("#id:")[-1]
                if "#id:" in url
                else f"desconocido_{indice}"
            )

            try:
                page.goto(url, wait_until="domcontentloaded", timeout=20000)
                random_sleep(
                    settings["delay_min_match"],
                    settings["delay_max_match"],
                )
            except Exception as error:
                logging.error(f"No se pudo abrir el partido {partido_id}: {error}")
                continue

            try:
                logging.info(
                    "Obteniendo alineaciones y estadísticas individuales..."
                )
                lineups_json, managers_json = obtener_lineups_y_managers(
                    page,
                    partido_id,
                )
                nombre_lineups = (
                    f"lineups_{liga.replace(' ', '_')}_R{ronda}_{partido_id}.json"
                )
                guardar_json(lineups_json, PLAYER_STATS_FOLDER, nombre_lineups)
                lineups_guardados += 1
                logging.info(f"Lineups guardado correctamente: {nombre_lineups}")

                if managers_json is not None:
                    nombre_managers = (
                        f"managers_{liga.replace(' ', '_')}_R{ronda}_"
                        f"{partido_id}.json"
                    )
                    guardar_json(
                        managers_json,
                        MANAGERS_FOLDER,
                        nombre_managers,
                    )
                    managers_guardados += 1
                    logging.info(
                        f"Managers guardado correctamente: {nombre_managers}"
                    )
            except Exception as error:
                logging.error(
                    f"No se pudo obtener lineups para el partido {partido_id}: {error}"
                )

            try:
                stats_json = obtener_estadisticas_equipo(page, partido_id)
                nombre_stats = (
                    f"stats_{liga.replace(' ', '_')}_R{ronda}_{partido_id}.json"
                )
                guardar_json(stats_json, OUTPUT_FOLDER, nombre_stats)
                estadisticas_guardadas += 1
                logging.info(
                    f"Estadísticas guardadas correctamente: {nombre_stats}"
                )
            except Exception as error:
                logging.error(
                    f"No se pudieron obtener estadísticas para el partido "
                    f"{partido_id}: {error}"
                )

            logging.info("Esperando antes del siguiente partido...")
            random_sleep(5, 10)

        logging.info(
            f"Lote finalizado: {lineups_guardados}/{len(urls_partidos)} lineups y "
            f"{managers_guardados}/{len(urls_partidos)} managers y "
            f"{estadisticas_guardadas}/{len(urls_partidos)} estadísticas guardadas."
        )
        logging.info("Cerrando navegador.")
        browser.close()
