import sys
import os
import json
import logging

# 1. Configuración de rutas
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(base_dir)

from utils.base import random_sleep
from utils.logger import setup_logger
from playwright.sync_api import sync_playwright
from utils.json_reader import load_config

# Inicializamos el logger
setup_logger()

# Carpetas de entrada y salida
INPUT_FOLDER = os.path.join(base_dir, 'data', 'urls_league_rounds')
OUTPUT_FOLDER = os.path.join(base_dir, 'data', 'matchs_stats')
os.makedirs(OUTPUT_FOLDER, exist_ok=True)


def procesar_archivo_ronda(nombre_archivo_json):

    config = load_config()
    settings = config['scraping_settings']

    ruta_input = os.path.join(INPUT_FOLDER, nombre_archivo_json)

    if not os.path.exists(ruta_input):
        logging.error(f"El archivo {ruta_input} no existe.")
        return

    # Cargamos el archivo JSON de origen
    with open(ruta_input, 'r', encoding='utf-8') as f:
        datos_ronda = json.load(f)

    urls_partidos = datos_ronda.get("urls", [])
    liga = datos_ronda.get("liga", "Desconocida")
    ronda = datos_ronda.get("ronda", 0)

    logging.info(f" Iniciando extracción para {liga} - Ronda {ronda}")
    logging.info(f" Total de partidos a procesar: {len(urls_partidos)}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, args=['--start-maximized'])
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            no_viewport=True
        )
        page = context.new_page()

        # Iteramos sobre cada URL de la lista
        for idx, url in enumerate(urls_partidos, start=1):
            logging.info(f"---")
            logging.info(f"⚽ Procesando partido {idx}/{len(urls_partidos)}")
            logging.info(f"🔗 URL: {url}")

            # Extraemos el ID del partido de la URL (ej: 12436873)
            # La URL termina en #id:12436873
            partido_id = url.split("#id:")[-1] if "#id:" in url else f"desconocido_{idx}"

            try:
                # Navegamos al partido
                page.goto(url, wait_until="domcontentloaded", timeout=20000)
                random_sleep(settings['delay_min_match'], settings['delay_max_match'])  # Pausa inicial para que cargue la interfaz

                logging.info("Buscando la pestaña de Estadísticas...")

                # OJO AQUÍ: Buscamos el botón de Estadísticas.
                # Sofascore a veces lo tiene en inglés (Statistics) o español (Estadísticas).
                # Usaremos un selector flexible o por href.
                btn_stats = page.locator('button[data-testid="tab-statistics"]')

                if not btn_stats.is_visible():
                    logging.warning(f"No se ve la pestaña estadísticas para el partido {partido_id}. Saltando...")
                    continue

                logging.info("Pestaña encontrada. Preparando la intercepción de red...")

                # Magia de Playwright: Esperamos a que la red responda con el archivo que tenga "statistics" en su URL
                with page.expect_response(lambda response: "statistics" in response.url and response.status == 200,
                                          timeout=15000) as response_info:
                    btn_stats.click()
                    logging.info("Clic realizado. Esperando que el servidor envíe el JSON...")

                # Capturamos la respuesta de la red
                stats_response = response_info.value
                stats_json = stats_response.json()

                # Guardamos el JSON atrapado
                nombre_salida = f"stats_{liga.replace(' ', '_')}_R{ronda}_{partido_id}.json"
                ruta_salida = os.path.join(OUTPUT_FOLDER, nombre_salida)

                with open(ruta_salida, 'w', encoding='utf-8') as f:
                    json.dump(stats_json, f, indent=4, ensure_ascii=False)

                logging.info(f"✅ ¡Estadísticas guardadas con éxito! Archivo: {nombre_salida}")

            except Exception as e:
                logging.error(f"❌ Fallo al procesar el partido {partido_id}: {e}")

            # Pausa ética larga antes de ir al siguiente partido de la lista
            logging.info("Tomando un respiro humano antes del siguiente partido...")
            random_sleep(5, 10)

        logging.info("🏁 Lote de partidos finalizado. Cerrando navegador.")
        browser.close()