"""Pruebas H1 en memoria y humo de solo lectura sobre 869 encuentros.

Ejecutar desde la raíz: python -m unittest ml_models.h1.test_features -v
"""

from contextlib import closing, contextmanager
import hashlib
from pathlib import Path
import sqlite3
import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd

from ml_models.analisis_volumen import conectar_solo_lectura
from ml_models.h1.features import (
    CONTEXTO,
    LINEAS,
    MERCADOS,
    SQL_BASE_H1,
    ajustar_umbrales_cv_h1,
    aplicar_filtro_elegibilidad_h1,
    construir_dataset_h1,
)


RAIZ = Path(__file__).resolve().parents[2]
DB_PATH = RAIZ / "database" / "oraculo.db"


def crear_historia(n: int = 18) -> pd.DataFrame:
    """Dos equipos alternan localía; cada mercado tiene valores distintos."""
    filas = []
    for jornada in range(1, n + 1):
        for equipo in (1, 2):
            valor = jornada if equipo == 1 else 2 * jornada + 2
            filas.append({
                "Id_partido": jornada,
                "Id_liga": 10,
                "Nombre_liga": "Liga sintética",
                "Temporada": "2026",
                "Ronda": jornada,
                "Fecha_hora_utc": pd.Timestamp("2026-01-01", tz="UTC")
                + pd.Timedelta(days=jornada),
                "Id_equipo": equipo,
                "Nombre_equipo": f"Equipo {equipo}",
                "Condicion_local": int(equipo == (1 if jornada % 2 else 2)),
                "Periodo": "ALL",
                **{m: float(valor + 5 * i) for i, m in enumerate(MERCADOS)},
                "Posesion_balon": float(40 + jornada),
                "Goles_esperados_xG": jornada / 10,
            })
    return pd.DataFrame(filas)


class FeaturesH1Test(unittest.TestCase):
    def setUp(self):
        self.base = crear_historia()

    def test_cero_fuga_en_t_y_pasado_cambia_solo_el_futuro(self):
        original = construir_dataset_h1(self.base)
        cambiado = self.base.copy()
        cambiado.loc[cambiado.Id_partido.eq(10), "Corners"] += 100
        nuevo = construir_dataset_h1(cambiado)
        entradas = [c for c in original if not c.startswith("target_")]
        pd.testing.assert_frame_equal(
            original.loc[:9, entradas], nuevo.loc[:9, entradas]
        )
        self.assertEqual(
            nuevo.loc[9, "target_Corners_total"],
            original.loc[9, "target_Corners_total"] + 200,
        )
        self.assertNotEqual(
            original.loc[10, "L_Corners_favor_mean_10"],
            nuevo.loc[10, "L_Corners_favor_mean_10"],
        )
        sin_corners = [c for c in original if "Corners" not in c]
        pd.testing.assert_frame_equal(
            original[sin_corners], nuevo[sin_corners]
        )

    def test_contexto_y_todos_los_mercados_tambien_se_desplazan(self):
        original = construir_dataset_h1(self.base)
        cambiado = self.base.copy()
        columnas = [*MERCADOS, *CONTEXTO]
        cambiado.loc[cambiado.Id_partido.eq(10), columnas] *= 0
        nuevo = construir_dataset_h1(cambiado)
        entradas = [c for c in original if not c.startswith("target_")]
        pd.testing.assert_frame_equal(
            original.loc[:9, entradas], nuevo.loc[:9, entradas]
        )
        for metrica in CONTEXTO:
            self.assertNotEqual(
                original.loc[10, f"L_{metrica}_mean_10"],
                nuevo.loc[10, f"L_{metrica}_mean_10"],
            )

    def test_localia_solo_usa_historia_del_mismo_rol(self):
        df = construir_dataset_h1(self.base).set_index("Id_partido")
        self.assertEqual(df.loc[7, "L_Corners_favor_rol_mean_5"], 3)
        self.assertEqual(df.loc[7, "V_Corners_favor_rol_mean_5"], 8)
        self.assertTrue(pd.isna(df.loc[6, "L_Corners_favor_rol_mean_5"]))
        self.assertEqual(df.loc[17, "L_Corners_favor_rol_mean_5"], 11)

    def test_min_periods_son_observaciones_previas_no_ceros(self):
        df = construir_dataset_h1(self.base)
        historia = [c for c in df if c.startswith(("L_", "V_"))]
        self.assertTrue(df.loc[:2, historia].isna().all().all())
        self.assertEqual(df.loc[3, "L_Corners_favor_mean_5"], 6)
        diez = [c for c in historia if c.endswith("_10")]
        self.assertTrue(df.loc[:4, diez].isna().all().all())
        self.assertTrue(df.loc[5, diez].notna().all())

    def test_ventanas_ddof_y_cruces_exactos_para_cada_mercado(self):
        df = construir_dataset_h1(self.base).set_index("Id_partido")
        for i, mercado in enumerate(MERCADOS):
            with self.subTest(mercado=mercado):
                # Partido 6: local=equipo 2, historia de jornadas 1 a 5.
                favor = np.array([4, 6, 8, 10, 12]) + 5 * i
                contra = np.array([1, 2, 3, 4, 5]) + 5 * i
                total = favor + contra
                for sentido, valores in (
                    ("favor", favor), ("contra", contra), ("partido", total),
                ):
                    self.assertAlmostEqual(
                        df.loc[6, f"L_{mercado}_{sentido}_mean_10"],
                        valores.mean(),
                    )
                    self.assertAlmostEqual(
                        df.loc[6, f"L_{mercado}_{sentido}_std_10"],
                        valores.std(ddof=1),
                    )
                self.assertAlmostEqual(df.loc[6, f"Exp_{mercado}_general"],
                                       11 + 10 * i)
                self.assertAlmostEqual(df.loc[6, f"Diff_{mercado}_general"], 5)
                self.assertAlmostEqual(df.loc[6, f"Match_CV_{mercado}"],
                                       np.sqrt(22.5) / (11 + 10 * i))
                self.assertAlmostEqual(df.loc[7, f"Exp_{mercado}_rol"],
                                       11 + 10 * i)
                # Partido 16: ventana 5 usa jornadas 11..15; ventana 10, 6..15.
                self.assertEqual(df.loc[16, f"L_{mercado}_favor_mean_5"],
                                 28 + 5 * i)
                self.assertEqual(df.loc[16, f"L_{mercado}_favor_mean_10"],
                                 23 + 5 * i)
        self.assertEqual(df.loc[6, "L_Posesion_balon_mean_10"], 43)
        self.assertAlmostEqual(df.loc[6, "L_Goles_esperados_xG_mean_10"], 0.3)

    def test_cruces_con_historias_diferentes_por_rival(self):
        base = crear_historia(7)
        segunda = crear_historia(6)
        segunda["Id_partido"] += 100
        segunda["Id_equipo"] += 2
        segunda["Nombre_equipo"] = segunda.Id_equipo.map(
            lambda x: f"Equipo {x}"
        )
        segunda[list(MERCADOS)] *= 2
        segunda.loc[segunda.Id_partido.eq(101) & segunda.Id_equipo.eq(3),
                    list(MERCADOS)] += 10
        # En el juego 7, equipo 1 recibe a equipo 3, con otra historia.
        visita = base.Id_partido.eq(7) & base.Id_equipo.eq(2)
        base.loc[visita, "Id_equipo"] = 3
        base.loc[visita, "Nombre_equipo"] = "Equipo 3"
        df = construir_dataset_h1(
            pd.concat([base, segunda], ignore_index=True)
        )
        fila = df.set_index("Id_partido").loc[7]
        # Equipo 3: favor=[12,4,6,8,10,12], contra=[8,12,16,20,24,28].
        self.assertAlmostEqual(fila.Exp_Corners_general,
                               (3.5 + 18) / 2 + (52 / 6 + 9) / 2)
        self.assertAlmostEqual(fila.Diff_Corners_general,
                               (3.5 + 18) / 2 - (52 / 6 + 9) / 2)
        self.assertEqual(fila.Exp_Corners_rol, (3 + 20) / 2 + (8 + 8) / 2)
        cv_local = np.std([5, 8, 11, 14, 17, 20], ddof=1) / 12.5
        cv_visita = np.std([20, 16, 22, 28, 34, 40], ddof=1) / (160 / 6)
        self.assertAlmostEqual(
            fila.Match_CV_Corners, (cv_local + cv_visita) / 2
        )

    def test_umbrales_solo_train_no_recalcula_en_test(self):
        train = pd.DataFrame({
            f"Match_CV_{m}": [0.1, 0.2, 0.3, 0.4, np.nan] for m in MERCADOS
        })
        test = pd.DataFrame({
            f"Match_CV_{m}": [0.325, 0.33, 99.0, np.nan] for m in MERCADOS
        })
        copia = test.copy(deep=True)
        umbrales = ajustar_umbrales_cv_h1(train)
        copia_umbrales = umbrales.copy()
        filtrado = aplicar_filtro_elegibilidad_h1(test, umbrales)
        for mercado in MERCADOS:
            self.assertAlmostEqual(umbrales[mercado], 0.325)
            self.assertEqual(
                filtrado[f"flag_elegible_h1_{mercado}"].tolist(),
                [True, False, False, False],
            )
            self.assertEqual(
                filtrado[f"flag_elegible_h1_{mercado}"].dtype, bool
            )
        self.assertEqual(umbrales, copia_umbrales)
        pd.testing.assert_frame_equal(test, copia)

    def test_umbral_ausente_vacio_y_percentil_invalido(self):
        df = pd.DataFrame({f"Match_CV_{m}": [np.nan] for m in MERCADOS})
        for train in (df, df.iloc[:0]):
            umbrales = ajustar_umbrales_cv_h1(train)
            self.assertTrue(all(np.isnan(u) for u in umbrales.values()))
            flags = aplicar_filtro_elegibilidad_h1(df, umbrales)
            self.assertFalse(flags.filter(like="flag_").any().any())
        for percentil in (-0.1, 1.1, np.nan):
            with self.assertRaises(ValueError):
                ajustar_umbrales_cv_h1(df, percentil)
        with self.assertRaisesRegex(ValueError, "Faltan umbrales"):
            aplicar_filtro_elegibilidad_h1(df, {})

    def test_targets_nulos_ceros_y_lineas(self):
        base = self.base.copy()
        for mercado, lineas in LINEAS.items():
            for partido, total in enumerate((0, *lineas, 100), start=1):
                base.loc[base.Id_partido.eq(partido), mercado] = np.floor(
                    total
                )
                base.loc[base.Id_partido.eq(partido) & base.Id_equipo.eq(2),
                         mercado] = 0
            ausente = base.Id_partido.eq(6) & base.Id_equipo.eq(2)
            base.loc[ausente, mercado] = np.nan
        df = construir_dataset_h1(base).set_index("Id_partido")
        for mercado, lineas in LINEAS.items():
            self.assertEqual(df.loc[1, f"target_{mercado}_total"], 0)
            self.assertTrue(
                df.loc[6].filter(like=f"target_{mercado}_").isna().all()
            )
            for linea in lineas:
                etiqueta = str(linea).replace(".", "_")
                columna = f"target_{mercado}_over_{etiqueta}"
                for partido in range(1, 6):
                    total = df.loc[partido, f"target_{mercado}_total"]
                    self.assertEqual(df.loc[partido, columna],
                                     int(total > linea))

    def test_cv_cero_y_nulos_en_ventanas(self):
        base = self.base.copy()
        base[list(MERCADOS)] = 0.0
        df = construir_dataset_h1(base)
        self.assertTrue(df.filter(like="_cv_10").isna().all().all())
        self.assertEqual(df.loc[5, "L_Corners_partido_std_10"], 0)
        base.loc[base.Id_partido.isin([1, 2, 3]), "Corners"] = np.nan
        df = construir_dataset_h1(base)
        self.assertTrue(pd.isna(df.loc[5, "L_Corners_favor_mean_10"]))
        self.assertEqual(df.loc[8, "L_Corners_favor_mean_10"], 0)
        self.assertTrue(pd.isna(df.loc[8, "Match_CV_Corners"]))

    def test_orden_ligas_temporadas_y_no_mutacion(self):
        otra = self.base.copy()
        otra["Id_liga"] = 20
        otra["Temporada"] = "2027"
        otra["Id_partido"] += 100
        otra["Fecha_hora_utc"] += pd.Timedelta(days=365)
        otra[list(MERCADOS)] += 100
        combinado = pd.concat([otra, self.base], ignore_index=True)
        combinado = combinado.sample(frac=1, random_state=5)
        copia = combinado.copy(deep=True)
        df = construir_dataset_h1(combinado)
        pd.testing.assert_frame_equal(combinado, copia)
        esperado = pd.concat([
            construir_dataset_h1(self.base), construir_dataset_h1(otra),
        ], ignore_index=True)
        pd.testing.assert_frame_equal(df, esperado)
        self.assertEqual(df.shape, (36, 150))
        self.assertFalse(df.columns.duplicated().any())
        self.assertTrue(df.columns[-16:].str.startswith("target_").all())
        self.assertFalse(any(c.endswith("_real") for c in df))
        filtrado = aplicar_filtro_elegibilidad_h1(
            df, ajustar_umbrales_cv_h1(df)
        )
        self.assertTrue(filtrado.columns[-16:].str.startswith("target_").all())

    def test_solo_all_y_dataframe_vacio(self):
        extra = self.base.copy()
        extra["Periodo"] = "2ND"
        extra[list(MERCADOS)] = 999.0
        df = construir_dataset_h1(pd.concat([self.base, extra]))
        pd.testing.assert_frame_equal(df, construir_dataset_h1(self.base))
        vacio = construir_dataset_h1(extra)
        self.assertEqual(vacio.shape, (0, 150))
        self.assertEqual(vacio.columns.tolist(), df.columns.tolist())

    def test_rechaza_pares_fechas_y_claves_invalidas(self):
        casos = [
            self.base.iloc[1:], pd.concat([self.base, self.base.iloc[:1]]),
        ]
        for columna, valor in (
            ("Fecha_hora_utc", pd.NaT), ("Condicion_local", 2),
            ("Id_liga", 30),
        ):
            base = self.base.copy()
            base.loc[0, columna] = valor
            casos.append(base)
        for base in casos:
            with self.subTest(caso=len(base)), self.assertRaises(ValueError):
                construir_dataset_h1(base)
        simultaneos = self.base.copy()
        simultaneos.loc[simultaneos.Id_partido.eq(2), "Fecha_hora_utc"] = (
            simultaneos.loc[0, "Fecha_hora_utc"]
        )
        with self.assertRaisesRegex(ValueError, "Cronología ambigua"):
            construir_dataset_h1(simultaneos)

    def test_sql_en_memoria_preserva_estadisticas_ausentes(self):
        base = crear_historia(2)
        stats = base[[
            "Id_partido", "Id_equipo", "Periodo", *MERCADOS, *CONTEXTO,
        ]]
        stats = stats.iloc[1:].copy()
        parcial = stats.copy()
        parcial["Periodo"] = "2ND"
        parcial[list(MERCADOS)] = 999
        with closing(sqlite3.connect(":memory:")) as conexion:
            tablas = {
                "PARTIDOS": base[["Id_partido", "Id_liga", "Ronda",
                                  "Fecha_hora_utc"]].drop_duplicates(),
                "LIGAS": base[["Id_liga", "Nombre_liga", "Temporada"]]
                .drop_duplicates(),
                "PARTIDOS_EQUIPOS": base[["Id_partido", "Id_equipo",
                                          "Condicion_local"]],
                "EQUIPOS": base[["Id_equipo", "Nombre_equipo"]]
                .drop_duplicates(),
                "PARTIDOS_ESTADISTICAS": pd.concat([stats, parcial]),
            }
            for nombre, tabla in tablas.items():
                tabla.to_sql(nombre, conexion, index=False)
            leido = pd.read_sql_query(SQL_BASE_H1, conexion)
        df = construir_dataset_h1(leido)
        self.assertEqual(len(df), 2)
        self.assertTrue(np.isnan(df.loc[0, "target_Corners_total"]))
        self.assertEqual(df.loc[1, "target_Corners_total"], 8)

    @unittest.skipUnless(DB_PATH.is_file(), "No existe database/oraculo.db")
    def test_humo_869_partidos_y_base_inalterada_solo_lectura(self):
        def huellas():
            resultado = {}
            for sufijo in ("", "-wal", "-shm", "-journal"):
                ruta = Path(str(DB_PATH) + sufijo)
                if ruta.exists():
                    with ruta.open("rb") as archivo:
                        digest = hashlib.file_digest(archivo, "sha256")
                    stat = ruta.stat()
                    resultado[sufijo] = (
                        digest.hexdigest(), stat.st_size, stat.st_mtime_ns,
                    )
            return resultado

        @contextmanager
        def conexion_verificada(raiz):
            with conectar_solo_lectura(raiz) as conexion:
                self.assertEqual(
                    conexion.execute("PRAGMA query_only").fetchone(), (1,)
                )
                yield conexion

        antes = huellas()
        with patch("ml_models.h1.features.conectar_solo_lectura",
                   side_effect=conexion_verificada), patch(
            "ml_models.analisis_volumen.sqlite3.connect", wraps=sqlite3.connect
        ) as conectar:
            df = construir_dataset_h1()
        self.assertEqual(antes, huellas())
        self.assertEqual(df.shape, (869, 150))
        self.assertFalse(df.columns.duplicated().any())
        self.assertTrue(df.Id_partido.is_unique)
        self.assertIn("?mode=ro", conectar.call_args.args[0])
        self.assertTrue(conectar.call_args.kwargs["uri"])


if __name__ == "__main__":
    unittest.main()
