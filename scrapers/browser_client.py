"""Sesión Chromium compartida, captura pasiva y respaldo JSON same-origin."""

import logging
from urllib.parse import urlsplit

from playwright.sync_api import sync_playwright


class BrowserClient:
    """Abre el navegador bajo demanda y lo recicla tras un bloque de trabajo."""

    def __init__(self, recycle_every):
        if type(recycle_every) is not int or recycle_every < 1:
            raise ValueError("El bloque de reciclaje debe ser un entero positivo.")
        self.recycle_every = recycle_every
        self.units = 0
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None

    def __enter__(self):
        return self

    def get_page(self):
        """Retorna (página, sesión_nueva); la unidad se confirma con finish_unit."""
        if self.page is not None and (
            self.units >= self.recycle_every or self.page.is_closed()
        ):
            self.recycle()
        if self.page is not None:
            return self.page, False
        try:
            if self.playwright is None:
                self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.launch(
                headless=False,
                args=[
                    "--start-maximized",
                    "--disable-blink-features=AutomationControlled",
                ],
                ignore_default_args=["--enable-automation"],
            )
            # Mantener el user agent nativo de Chromium y sus client hints.
            self.context = self.browser.new_context(no_viewport=True)
            self.page = self.context.new_page()
            return self.page, True
        except Exception:
            self.recycle()
            raise

    def finish_unit(self):
        self.units += 1

    def recycle(self):
        """Libera contexto y navegador incluso si alguno ya se cerró."""
        for resource in (self.context, self.browser):
            if resource is not None:
                try:
                    resource.close()
                except Exception as error:
                    logging.warning("Error cerrando navegador: %s", error)
        self.context = self.browser = self.page = None
        self.units = 0

    def __exit__(self, exc_type, exc_value, traceback):
        self.recycle()
        if self.playwright is not None:
            try:
                self.playwright.stop()
            finally:
                self.playwright = None


def limpiar_overlays(page):
    """Cierra consentimientos conocidos y oculta capas publicitarias invasivas."""
    for selector in (
        "#onetrust-accept-btn-handler",
        "button.fc-cta-consent",
        "button[aria-label='Close ad']",
        "button[aria-label='Close']",
    ):
        try:
            boton = page.locator(selector).first
            if boton.is_visible():
                boton.click(timeout=1000)
        except Exception as error:
            logging.debug("No se pudo cerrar overlay %s: %s", selector, error)
    try:
        page.evaluate("""() => {
            for (const selector of ['#goog-content-pause-scrim',
                    '#onetrust-banner-sdk', '.fc-consent-root',
                    'ins.adsbygoogle[data-vignette-loaded="true"]']) {
                document.querySelectorAll(selector).forEach(el => {
                    el.style.setProperty('display', 'none', 'important');
                    el.style.setProperty('pointer-events', 'none', 'important');
                });
            }
        }""")
    except Exception as error:
        logging.debug("No se pudieron ocultar overlays: %s", error)


def click_defensivo(page, locator):
    """Reintenta un clic con force si un overlay intercepta el puntero."""
    limpiar_overlays(page)
    try:
        locator.click(timeout=2500)
    except Exception:
        limpiar_overlays(page)
        locator.click(force=True, timeout=2500)


def fetch_json(page, endpoint):
    """Consulta JSON con cookies del navegador; acota la espera a 15 segundos.

    El endpoint debe ser una ruta /api/v1/ del origen actual de Sofascore.
    No garantiza eludir rechazos HTTP: los informa para el reporte del lote.
    """
    if not endpoint.startswith("/api/v1/"):
        raise ValueError("El endpoint debe ser una ruta API relativa al origen.")
    return page.evaluate("""async (url) => {
        if (location.origin !== 'https://www.sofascore.com') {
            throw new Error('La página no está en el origen de Sofascore');
        }
        const controller = new AbortController();
        const timer = setTimeout(() => controller.abort(), 15000);
        try {
            const response = await fetch(url, {
                credentials: 'include',
                headers: {'Accept': 'application/json'},
                signal: controller.signal
            });
            if (!response.ok) throw new Error(`HTTP ${response.status}: ${url}`);
            return await response.json();
        } finally {
            clearTimeout(timer);
        }
    }""", endpoint)


def registrar_captura(page, recursos):
    """Captura endpoints exactos: {nombre: (ruta, validador)}; no guarda disco."""
    capturas = {}

    def listener(response):
        ruta = urlsplit(response.url).path.rstrip("/")
        for nombre, (endpoint, validar) in recursos.items():
            if ruta != endpoint or response.status != 200 or nombre in capturas:
                continue
            try:
                datos = response.json()
                if validar(datos):
                    capturas[nombre] = datos
            except Exception as error:
                logging.warning("Respuesta JSON inválida en %s: %s", ruta, error)

    page.on("response", listener)
    return capturas, listener


def esperar_capturas(page, capturas, requeridos, timeout_ms=1500):
    """Bombea eventos de Playwright sin esperar una respuesta XHR obligatoria."""
    for _ in range(0, timeout_ms, 250):
        if all(nombre in capturas for nombre in requeridos):
            break
        page.wait_for_timeout(250)


def retirar_captura(page, listener):
    try:
        page.remove_listener("response", listener)
    except Exception as error:
        logging.debug("No se pudo retirar listener: %s", error)
