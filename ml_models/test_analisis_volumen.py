"""Regresiones de integridad analítica con SQLite temporal; no toca la base real.

Ejecutar: python -m unittest ml_models.test_analisis_volumen -v
"""

from pathlib import Path
from contextlib import closing
import sqlite3
import tempfile
import unittest

import numpy as np
import pandas as pd

from ml_models.analisis_volumen import (
    ESQUEMA, METRICAS, MERCADOS, SQL_EQUIPO_PERIODO, SQL_TOTALES,
    ajustar_conteos, auditar, conectar_solo_lectura, construir_totales,
    describir, encontrar_raiz, limpiar_equipo, ranking_estabilidad,
)


class AnalisisVolumenTest(unittest.TestCase):
    def setUp(self):
        self.temporal = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporal.cleanup)
        self.raiz = Path(self.temporal.name)
        (self.raiz / "database").mkdir()
        (self.raiz / "ml_models").mkdir()
        self.db_path = self.raiz / "database" / "oraculo.db"
        with closing(sqlite3.connect(self.db_path)) as conexion, conexion:
            for tabla, columnas in ESQUEMA.items():
                # Esquema mínimo deliberadamente sin constraints para probar auditorías.
                definiciones = ", ".join(f'"{c}"' for c in columnas)
                conexion.execute(f'CREATE TABLE "{tabla}" ({definiciones})')
            conexion.execute("INSERT INTO PAIS VALUES (1, 'TST', 'Prueba')")
            conexion.execute("INSERT INTO LIGAS VALUES (1,1,1,'Liga prueba','2026')")
            conexion.executemany("INSERT INTO EQUIPOS VALUES (?,1,?,NULL)",
                                 [(1, "Local"), (2, "Visita")])
            conexion.execute("""INSERT INTO PARTIDOS
                (Id_partido, Id_liga, Ronda, Fecha_hora_utc) VALUES (1,1,1,'2026-01-01')""")
            conexion.executemany("INSERT INTO PARTIDOS_EQUIPOS VALUES (1,?,?,NULL)",
                                 [(1, 1), (2, 0)])
            conexion.executemany("""INSERT INTO PARTIDOS_ESTADISTICAS
                (Id_partido, Id_equipo, Periodo, Corners, Faltas) VALUES (1,?,?,?,?)""",
                [(1, "ALL", 0, 4), (2, "ALL", 0, None),
                 (1, "2ND", 2, 3), (2, "2ND", 3, 4)])

    def leer_equipo(self):
        with conectar_solo_lectura(self.raiz) as conexion:
            return pd.read_sql_query(SQL_EQUIPO_PERIODO, conexion)

    def test_rutas_y_lectura_estricta(self):
        self.assertEqual(encontrar_raiz(self.raiz / "ml_models"), self.raiz)
        with conectar_solo_lectura(self.raiz / "ml_models") as conexion:
            with self.assertRaises(sqlite3.OperationalError):
                conexion.execute("DELETE FROM PARTIDOS")
        # La conexión del gestor se cierra incluso después de errores.
        with self.assertRaises(sqlite3.ProgrammingError):
            conexion.execute("SELECT 1")
        self.db_path.unlink()
        with self.assertRaises(FileNotFoundError):
            with conectar_solo_lectura(self.raiz):
                pass
        self.assertFalse(self.db_path.exists())

    def test_totales_con_nulos_ceros_y_periodos_ausentes(self):
        equipo, _ = limpiar_equipo(self.leer_equipo())
        total = construir_totales(equipo).set_index("Periodo")
        self.assertEqual(total.loc["ALL", "Corners"], 0)
        self.assertTrue(pd.isna(total.loc["ALL", "Faltas"]))
        self.assertTrue(pd.isna(total.loc["1ST", "Corners"]))
        self.assertEqual(total.loc["2ST", "Corners"], 5)
        self.assertEqual(set(equipo.loc[equipo.Periodo.eq("2ST"), "Periodo_origen"]), {"2ND"})
        with conectar_solo_lectura(self.raiz) as conexion:
            sql = pd.read_sql_query(SQL_TOTALES, conexion).set_index("Periodo")
        pd.testing.assert_series_equal(sql.Corners, total.Corners, check_dtype=False)
        incompleto = equipo.loc[equipo.Condicion_local.eq(1)]
        self.assertTrue(construir_totales(incompleto).Corners.isna().all())

    def test_colision_de_alias_y_participantes_invalidos(self):
        with conectar_solo_lectura(self.raiz) as conexion:
            auditar(conexion)
        with closing(sqlite3.connect(self.db_path)) as conexion, conexion:
            conexion.execute("""INSERT INTO PARTIDOS_ESTADISTICAS
                (Id_partido, Id_equipo, Periodo) VALUES (1,1,'2ST')""")
        with conectar_solo_lectura(self.raiz) as conexion:
            with self.assertRaisesRegex(ValueError, "duplicadas"):
                auditar(conexion)
        with closing(sqlite3.connect(self.db_path)) as conexion, conexion:
            conexion.execute("DELETE FROM PARTIDOS_EQUIPOS WHERE Id_equipo=2")
        with conectar_solo_lectura(self.raiz) as conexion:
            with self.assertRaisesRegex(ValueError, "condiciones"):
                auditar(conexion)

    def test_saneamiento_no_confunde_cero_con_ausencia(self):
        equipo = self.leer_equipo()
        equipo.loc[0, "Corners"] = -1
        equipo.loc[1, "Corners"] = 1.5
        equipo.loc[2, "Posesion_balon"] = 101
        limpio, incidencias = limpiar_equipo(equipo)
        self.assertEqual(len(incidencias), 3)
        self.assertTrue(limpio.loc[[0, 1], "Corners"].isna().all())
        self.assertTrue(pd.isna(limpio.loc[2, "Posesion_balon"]))
        self.assertTrue(limpio.Corners.eq(0).any())

    def test_muestras_pequenas_y_sobredispersion(self):
        self.assertEqual(ajustar_conteos(pd.Series(dtype=float))["N"], 0)
        ceros = ajustar_conteos(pd.Series([0, 0, 0]))
        self.assertEqual(ceros["LogL_Poisson"], 0)
        self.assertTrue(np.isnan(ceros["NB_r"]))
        self.assertTrue(np.isnan(ajustar_conteos(pd.Series([2, 3, 2]))["NB_r"]))
        sobredispersos = ajustar_conteos(pd.Series([0, 0, 0, 10, 20]))
        self.assertGreater(sobredispersos["Razon_var_media"], 1)
        self.assertGreater(sobredispersos["NB_r"], 0)
        self.assertTrue(0 < sobredispersos["NB_p"] < 1)
        equipo, _ = limpiar_equipo(self.leer_equipo())
        tabla = ranking_estabilidad(equipo, ["Id_equipo", "Periodo"], min_n=30)
        self.assertFalse(tabla.Elegible.any())
        self.assertTrue(tabla.Puesto.isna().all())
        cero = describir(equipo, ["Periodo"]).query("Periodo == 'ALL' and Mercado == 'Corners'")
        self.assertTrue(cero.CV.isna().all())


if __name__ == "__main__":
    unittest.main()
