"""Verificación offline: python -m unittest scrapers.test_resiliencia -v.

Todos los artefactos se escriben en TemporaryDirectory; no se abre SQLite.
"""

from contextlib import ExitStack
from pathlib import Path
import tempfile
import unittest
from unittest.mock import MagicMock, patch

import main
from scrapers import artifact_store as store
from scrapers import browser_client as browser
from scrapers import match_crawler as crawler
from scrapers import stats_scraper as scraper
from utils.json_reader import load_config, parsear_rondas_objetivo


PAYLOADS = {
    "stats": {"statistics": [{"period": "ALL", "groups": []}]},
    "lineups": {"home": {"players": []}},
    "managers": {"awayManager": {"id": 10}},
}


class ResilienciaTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.raw = Path(self.temporary.name)
        self.nombre = "urls_england_premier-league_25-26_ronda_38.json"
        self.urls_path = self.raw / "urls_league_rounds" / self.nombre
        self.events_path = self.raw / "league_events" / self.nombre.replace("urls_", "round_events_", 1)
        self.settings = {
            "delay_min_match": 0, "delay_max_match": 0,
            "delay_min_seconds": 0, "delay_max_seconds": 0,
            "ronda_objetivo": [1, 2, 3],
        }
        self.config = {
            "scraping_settings": self.settings,
            "leagues": [{"name": "Premier League", "country": "England",
                         "tournament_id": 17,
                         "seasons": [{"year": "25/26", "season_id": 76986}]}],
        }
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        for modulo in (scraper, main):
            self.stack.enter_context(patch.object(modulo, "RAW_DIR", self.raw))
            self.stack.enter_context(patch.object(modulo, "load_config", return_value=self.config))
        self.stack.enter_context(patch.object(scraper, "INPUT_FOLDER", self.urls_path.parent))
        self.stack.enter_context(patch.object(main, "URLS_DIR", self.urls_path.parent))
        self.stack.enter_context(patch.object(main, "EVENTS_DIR", self.events_path.parent))

    def fixture(self, statuses):
        eventos = [{"id": pid, "slug": "home-away", "customId": "abc",
                    "status": {"type": estado}}
                   for pid, estado in enumerate(statuses, 1)]
        datos = {"events": eventos}
        store.guardar_json_atomico(datos, self.events_path)
        store.guardar_json_atomico({
            "liga": "Premier League", "ronda": 38,
            "urls": crawler.construir_urls_eventos(datos),
        }, self.urls_path)
        return eventos

    def artefactos(self, pid, tipos=PAYLOADS):
        rutas = store.rutas_artefactos(self.raw, "Premier League", 38, str(pid))
        for tipo in tipos:
            store.guardar_json_atomico(PAYLOADS[tipo], rutas[tipo])
        return rutas

    def test_parser_y_config_opcional(self):
        for valor, esperado in [(38, [38]), ([1, 2, 3], [1, 2, 3]),
                                ("1-38", list(range(1, 39))),
                                ("1,3,5", [1, 3, 5]), (" 1 - 2 ", [1, 2]),
                                ([2, 1, 2], [2, 1])]:
            with self.subTest(valor=valor):
                self.assertEqual(parsear_rondas_objetivo(valor), esperado)
        for invalido in [0, -1, True, None, 1.5, [], [1, False], ["1"],
                         "", "0-2", "3-1", "1,", "1,,2", "1-2,4", "1.5", {}]:
            with self.subTest(invalido=invalido), self.assertRaises(ValueError):
                parsear_rondas_objetivo(invalido)
        ruta = self.raw / "config.json"
        store.guardar_json_atomico(self.config, ruta)
        self.assertEqual(load_config(ruta), self.config)

    def test_urls_deduplicadas_y_estados(self):
        eventos = self.fixture(["finished", "postponed", "canceled", "notstarted"])
        datos = {"events": eventos + [eventos[0], {}, None]}
        urls = crawler.construir_urls_eventos(datos)
        self.assertEqual(len(urls), 4)
        self.assertEqual(urls[0], "https://www.sofascore.com/football/match/home-away/abc#id:1")
        self.assertEqual(store.ids_finalizados(datos), {"1"})
        self.assertEqual(crawler.construir_urls_eventos({"events": []}), [])
        with self.assertRaises(ValueError):
            crawler.construir_urls_eventos({"events": {}})

    def test_auditoria_corruptos_vacios_y_completos(self):
        self.fixture(["finished", "finished", "finished", "postponed"])
        self.artefactos(1)
        rutas = self.artefactos(2, ["lineups"])
        rutas["stats"].write_text("{invalido", encoding="utf-8")
        rutas["managers"].write_text("", encoding="utf-8")
        resumen = store.auditar_archivo_ronda(self.urls_path)
        self.assertEqual(resumen["total"], 4)
        self.assertEqual(resumen["omitidos_existentes"], 1)
        self.assertEqual(resumen["omitidos_no_finalizados"], 1)
        self.assertEqual(resumen["incompletos"][0]["faltantes"], ["stats", "managers"])
        self.assertEqual(len(resumen["incompletos"]), 2)
        for tipo in PAYLOADS:
            self.assertFalse(store.artefacto_valido({}, tipo))
            self.assertFalse(store.artefacto_valido(None, tipo))
            self.assertTrue(store.artefacto_valido(PAYLOADS[tipo], tipo))
        self.assertFalse(store.artefacto_valido({"statistics": []}, "stats"))
        self.assertFalse(store.artefacto_valido({"home": None}, "lineups"))
        self.assertFalse(store.artefacto_valido({"homeManager": None}, "managers"))

    def test_sin_eventos_y_eventos_invalidos(self):
        self.fixture(["finished", "postponed"])
        self.events_path.unlink()
        self.assertEqual(len(store.auditar_archivo_ronda(self.urls_path)["incompletos"]), 2)
        store.guardar_json_atomico({"events": None}, self.events_path)
        with patch.object(browser, "sync_playwright") as runtime:
            with self.assertRaises(ValueError):
                scraper.procesar_archivo_ronda(self.nombre)
            runtime.assert_not_called()

    def test_idempotencia_no_inicia_playwright(self):
        self.fixture(["finished", "notstarted"])
        rutas = self.artefactos(1)
        antes = {tipo: ruta.read_bytes() for tipo, ruta in rutas.items()}
        with patch.object(browser, "sync_playwright") as runtime:
            resumen = scraper.procesar_archivo_ronda(self.nombre)
            runtime.assert_not_called()
        self.assertEqual(resumen["omitidos_existentes"], 1)
        self.assertEqual(resumen["omitidos_no_finalizados"], 1)
        self.assertEqual(resumen["incompletos"], [])
        self.assertEqual(antes, {tipo: ruta.read_bytes() for tipo, ruta in rutas.items()})

    def test_descarga_granular_y_reintento_idempotente(self):
        self.fixture(["finished", "finished", "postponed"])
        rutas = self.artefactos(1, ["stats", "lineups"])
        stats_antes = rutas["stats"].read_bytes()
        page = MagicMock()
        with patch.object(scraper, "BrowserClient") as cliente, \
                patch.object(scraper, "fetch_json", return_value=PAYLOADS["managers"]) as fetch:
            cliente.return_value.__enter__.return_value.get_page.return_value = (page, True)
            resumen = scraper.procesar_archivo_ronda(self.nombre, solo_ids=[1])
            fetch.assert_called_once_with(page, "/api/v1/event/1/managers")
        self.assertEqual(resumen["completos"], 1)
        self.assertEqual(resumen["total"], 1)
        self.assertEqual(rutas["stats"].read_bytes(), stats_antes)
        with patch.object(browser, "sync_playwright") as runtime:
            resumen = scraper.procesar_archivo_ronda(self.nombre, solo_ids=[1])
            runtime.assert_not_called()
        self.assertEqual(resumen["omitidos_existentes"], 1)

    def test_listener_antes_de_goto_y_sin_fetch_si_capturado(self):
        self.fixture(["finished"])
        partido = store.inspeccionar_ronda(self.urls_path)[0]
        page = MagicMock()
        def navegar(*args, **kwargs):
            page.on.assert_called_once()
            listener = page.on.call_args.args[1]
            for tipo, recurso in scraper.RECURSOS.items():
                respuesta = MagicMock(status=200)
                respuesta.url = f"https://www.sofascore.com/api/v1/event/1/{recurso}"
                respuesta.json.return_value = PAYLOADS[tipo]
                listener(respuesta)
        page.goto.side_effect = navegar
        with patch.object(scraper, "fetch_json") as fetch:
            self.assertEqual(scraper._descargar_faltantes(page, partido), 3)
            fetch.assert_not_called()
        page.remove_listener.assert_called_once()

    def test_respuestas_invalidas_no_se_guardan_y_fallos_aislados(self):
        self.fixture(["finished"])
        partido = store.inspeccionar_ronda(self.urls_path)[0]
        page = MagicMock()
        page.goto.side_effect = RuntimeError("timeout simulado")
        with patch.object(scraper, "fetch_json", side_effect=[{}, RuntimeError("403"), PAYLOADS["managers"]]):
            self.assertEqual(scraper._descargar_faltantes(page, partido), 1)
        self.assertFalse(partido["rutas"]["stats"].exists())
        self.assertFalse(partido["rutas"]["lineups"].exists())
        self.assertTrue(partido["rutas"]["managers"].exists())
        page.remove_listener.assert_called_once()

    def test_circuit_breaker_y_reporte(self):
        self.fixture(["finished"] * 4)
        with patch.object(scraper, "BrowserClient") as factory, \
                patch.object(scraper, "_descargar_faltantes", return_value=0), \
                patch.object(scraper, "random_sleep") as dormir:
            cliente = factory.return_value.__enter__.return_value
            cliente.get_page.return_value = (MagicMock(), False)
            resumen = scraper.procesar_archivo_ronda(self.nombre)
            cliente.recycle.assert_called_once()
            dormir.assert_any_call(60, 90)
            self.assertEqual(cliente.finish_unit.call_count, 4)
        self.assertEqual(len(resumen["incompletos"]), 4)

    def test_browser_recicla_y_conserva_user_agent_nativo(self):
        with patch.object(browser, "sync_playwright") as runtime:
            playwright = runtime.return_value.start.return_value
            page = playwright.chromium.launch.return_value.new_context.return_value.new_page.return_value
            page.is_closed.return_value = False
            with browser.BrowserClient(2) as cliente:
                self.assertTrue(cliente.get_page()[1])
                cliente.finish_unit()
                self.assertFalse(cliente.get_page()[1])
                cliente.finish_unit()
                self.assertTrue(cliente.get_page()[1])
            self.assertEqual(playwright.chromium.launch.call_count, 2)
            opciones = playwright.chromium.launch.call_args.kwargs
            self.assertFalse(opciones["headless"])
            self.assertEqual(opciones["ignore_default_args"], ["--enable-automation"])
            self.assertNotIn("user_agent", playwright.chromium.launch.return_value.new_context.call_args.kwargs)
            playwright.stop.assert_called_once()

    def test_interceptor_no_confunde_rondas_1_y_10(self):
        page = MagicMock()
        capturas, listener = browser.registrar_captura(
            page, {"events": ("/api/v1/events/round/1", store.eventos_validos)}
        )
        respuesta = MagicMock(status=200)
        respuesta.url = "https://www.sofascore.com/api/v1/events/round/10"
        respuesta.json.return_value = {"events": []}
        listener(respuesta)
        self.assertEqual(capturas, {})
        respuesta.url = "https://www.sofascore.com/api/v1/events/round/1?x=1"
        listener(respuesta)
        self.assertEqual(capturas, {"events": {"events": []}})

    def test_crawler_multironda_y_reapertura_solo_al_reciclar(self):
        for sesiones, visitas in [([True, False, False], 1), ([True, False, True], 2)]:
            with self.subTest(sesiones=sesiones), \
                    patch.object(crawler, "load_config", return_value=self.config), \
                    patch.object(crawler, "data_dir", self.urls_path.parent), \
                    patch.object(crawler, "raw_league_events_dir", self.events_path.parent), \
                    patch.object(crawler, "BrowserClient") as factory, \
                    patch.object(crawler, "_seleccionar_ronda", side_effect=RuntimeError("overlay")), \
                    patch.object(crawler, "fetch_json", return_value={"events": []}) as fetch, \
                    patch.object(crawler, "random_sleep"):
                page = MagicMock()
                factory.return_value.__enter__.return_value.get_page.side_effect = [(page, nueva) for nueva in sesiones]
                crawler.run_url_explorer()
                self.assertEqual(page.goto.call_count, visitas)
                self.assertEqual(fetch.call_count, 3)
                self.assertEqual(page.remove_listener.call_count, 3)
                for ronda in (1, 2, 3):
                    archivo = self.urls_path.parent / self.nombre.replace("38.json", f"{ronda}.json")
                    self.assertEqual(store.leer_json(archivo)["urls"], [])






    def test_auditoria_reintenta_solo_pendientes_y_reaudita(self):
        self.fixture(["finished", "finished", "notstarted"])
        self.artefactos(1)
        with patch.object(main, "procesar_archivo_ronda") as procesar:
            resultado = main.auditar_y_reintentar_pendientes(ejecutar_reintento=False)
            procesar.assert_not_called()
            self.assertEqual([p["partido_id"] for p in resultado["pendientes"]], ["2"])
            procesar.side_effect = lambda *args, **kwargs: self.artefactos(2)
            resultado = main.auditar_y_reintentar_pendientes()
            procesar.assert_called_once_with(self.nombre, solo_ids=["2"])
            self.assertEqual(resultado["pendientes"], [])
        (self.urls_path.parent / "urls_corrupto.json").write_text("{", encoding="utf-8")
        resultado = main.auditar_y_reintentar_pendientes(ejecutar_reintento=False)
        self.assertEqual(len(resultado["errores"]), 1)
        self.assertEqual(len(resultado["archivos"]), 1)

    def test_flujo_multironda_sin_sqlite(self):
        with patch.object(main, "run_url_explorer") as explorar, \
                patch.object(main.os.path, "exists", return_value=True), \
                patch.object(main, "procesar_archivo_ronda", return_value={"incompletos": []}) as procesar, \
                patch.object(main, "ejecutar_etl_desde_eventos") as etl:
            self.assertEqual(main.ejecutar_flujo_completo(), [])
            explorar.assert_called_once_with(rondas_override=[1, 2, 3])
            self.assertEqual(procesar.call_count, 3)
            self.assertEqual([c.kwargs["ronda_filtro"] for c in etl.call_args_list], [1, 2, 3])

    def test_auditoria_preserva_pendientes_si_falla_reintento(self):
        self.fixture(["finished"])
        with patch.object(main, "procesar_archivo_ronda", side_effect=OSError("fallo")):
            resultado = main.auditar_y_reintentar_pendientes(self.nombre)
        self.assertEqual(len(resultado["errores"]), 1)
        self.assertEqual(len(resultado["pendientes"]), 1)

    def test_cli_retry_con_y_sin_archivo(self):
        for argumentos, esperado in [(["--retry-pending"], None),
                                     (["--retry-pending", self.nombre], self.nombre)]:
            with patch("sys.argv", ["main.py"] + argumentos), \
                    patch.object(main, "setup_logger"), \
                    patch.object(main, "auditar_y_reintentar_pendientes") as auditar:
                main.main()
                auditar.assert_called_once_with(esperado)


if __name__ == "__main__":
    unittest.main()
