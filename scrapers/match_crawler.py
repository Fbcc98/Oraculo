import sys
import os
import json
import logging

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(base_dir)

from utils.json_reader import load_config
from utils.base import random_sleep
from utils.logger import setup_logger  # <--- Importamos nuestro nuevo módulo
from playwright.sync_api import sync_playwright

setup_logger()

data_dir = os.path.join(base_dir, 'data', 'urls_league_rounds')
os.makedirs(data_dir, exist_ok=True)

def run_url_explorer():
    logging.info("Iniciando Oráculo - Explorador de URLs...")
    config = load_config()
    settings = config['scraping_settings']
    leagues = config['leagues']
    ronda_objetivo = settings.get('ronda_objetivo', 1)

    with sync_playwright() as p:
        logging.info("Levantando navegador Chromium...")
        browser = p.chromium.launch(headless=False,args=['--start-maximized'])

        context = browser.new_context(
            user_agent=settings['user_agent_default'],
            no_viewport = True
        )
        page = context.new_page()
        logging.info("Navegador iniciado correctamente.")

        for league in leagues:
            logging.info("=======================================")
            logging.info(f"🏆 Explorando Liga: {league['name']}")

            for season in league['seasons']:
                country = league['country'].lower()
                league_name_url = league['name'].lower().replace(" ", "-")

                logging.info(f"📅 Temporada {season['year']} | Buscando URLs de la Ronda {ronda_objetivo}...")

                url = f"https://www.sofascore.com/tournament/football/{country}/{league_name_url}/{league['tournament_id']}#id:{season['season_id']}"
                logging.info("Navegando a la URL base de la liga...")

                try:
                    page.goto(url, wait_until="domcontentloaded", timeout=15000)
                    logging.info("Página principal cargada con éxito.")
                except Exception as e:
                    logging.error(f"No se pudo cargar la URL principal: {e}")
                    continue

                random_sleep(settings['delay_min_seconds'], settings['delay_max_seconds'])

                logging.info("Buscando y cerrando banners de cookies/publicidad...")

                try:
                    logging.info("Localizando el combobox de Rondas en el DOM...")

                    random_sleep(settings['delay_min_seconds'], settings['delay_max_seconds'])

                    btn_ronda = page.get_by_role("combobox", name="Select item in event list")
                    btn_ronda.wait_for(state="visible", timeout=15000)
                    logging.info("Combobox 'btn_ronda' localizado.")

                    nombre_ronda_buscar = f"Round {ronda_objetivo}"
                    logging.info(f"Verificando si la opción '{nombre_ronda_buscar}' está visible...")

                    if not page.get_by_role("option", name=nombre_ronda_buscar, exact=True).is_visible():
                        logging.info("Desplegando el menú de rondas...")
                        btn_ronda.click()
                        random_sleep(settings['delay_min_seconds'], settings['delay_max_seconds'])

                    logging.info(f"Haciendo click en '{nombre_ronda_buscar}'...")
                    page.get_by_role("option", name=nombre_ronda_buscar, exact=True).click()
                    logging.info(f"Filtro '{nombre_ronda_buscar}' aplicado. Esperando que carguen los partidos...")

                    random_sleep(settings['delay_min_seconds'], settings['delay_max_seconds'])

                except Exception as e:
                    logging.error(f"Fallo durante la interacción con el menú de Rondas: {e}")
                    logging.info("Saltando a la siguiente temporada...")
                    continue

                try:
                    logging.info("Buscando enlaces de partidos dentro del contenedor de la ronda...")
                    contenedor_ronda = page.locator('#tabpanel-round')
                    enlaces_elementos = contenedor_ronda.locator('a[href*="/match/"]').all()

                    if not enlaces_elementos:
                        logging.warning("No se encontró el contenedor '#tabpanel-round', buscando de forma acotada...")
                        enlaces_elementos = page.locator(
                            'div[class*="unique-tournament"] ~ a[href*="/match/"], a.d_block[href*="/match/"]').all()

                    if not enlaces_elementos:
                        logging.warning("No se encontraron elementos de partidos válidos.")
                        continue

                    urls_extraidas = []
                    for elemento in enlaces_elementos:
                        href = elemento.get_attribute('href')
                        if href and "/match/" in href:
                            link_completo = f"https://www.sofascore.com{href}" if href.startswith('/') else href
                            if link_completo not in urls_extraidas:
                                urls_extraidas.append(link_completo)

                    logging.info(
                        f"Extracción finalizada con éxito. {len(urls_extraidas)} enlaces únicos de partidos capturados.")

                except Exception as e:
                    logging.error(f"Fallo al extraer los enlaces del DOM: {e}")
                    continue

                try:
                    if urls_extraidas:
                        logging.info("Escribiendo datos en archivo JSON...")
                        urls_unicas = list(set(urls_extraidas))

                        temporada_limpia = season['year'].replace("/", "-")

                        nombre_archivo = f"urls_{country}_{league_name_url}_{temporada_limpia}_ronda_{ronda_objetivo}.json"
                        ruta_archivo = os.path.join(data_dir, nombre_archivo)

                        datos_a_guardar = {
                            "liga": league['name'],
                            "pais": country,
                            "temporada": season['year'],
                            "ronda": ronda_objetivo,
                            "urls": urls_unicas
                        }

                        with open(ruta_archivo, 'w', encoding='utf-8') as f:
                            json.dump(datos_a_guardar, f, indent=4, ensure_ascii=False)

                        logging.info(f"Guardado correctamente en: {ruta_archivo}")
                    else:
                        logging.warning(f"No se encontraron URLs para guardar en la Ronda {ronda_objetivo}.")

                except Exception as e:
                    logging.error(f"Fallo al intentar guardar el archivo JSON: {e}")

        logging.info("Script Explorador finalizado. Cerrando navegador.")
        browser.close()