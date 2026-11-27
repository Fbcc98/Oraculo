"""Pruebas sintéticas del baseline y humo SQLite estrictamente de lectura."""

import hashlib
from pathlib import Path
import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd
from scipy import stats

from ml_models.h1.features import ajustar_umbrales_cv_h1
from ml_models.h1.model import (
    ALPHA_POISSON,
    LINEAS_BINARIAS_H1,
    MERCADOS_H1,
    METRICAS,
    TEMPORADAS_H1,
    ModeloBinomialNegativaH1,
    ModeloPoissonH1,
    NaiveMedia,
    dividir_temporalmente_h1,
    entrenar_modelos_h1,
    evaluar_modelo_h1,
    ejecutar_baseline_h1,
    predictoras_h1,
    preparar_mercado_h1,
    probabilidades_over_h1,
)


DB_PATH = Path(__file__).resolve().parents[2] / "database" / "oraculo.db"


def crear_dataset():
    """Tres temporadas con señales, nulos y dispersión reproducibles."""
    rng = np.random.default_rng(47)
    bloques = []
    for i, temporada in enumerate(TEMPORADAS_H1.values()):
        n = (240, 80, 50)[i]
        df = pd.DataFrame({
            "Id_partido": np.arange(n) + 1000 * i,
            "Temporada": temporada,
            "Fecha_hora_utc": pd.date_range(f"{2024 + i}-08-01", periods=n,
                                            tz="UTC"),
        })
        for mercado, media in zip(MERCADOS_H1, (10, 34, 22)):
            for columna in predictoras_h1(mercado):
                if columna not in df:
                    df[columna] = rng.normal(size=n)
            df[f"Match_CV_{mercado}"] = rng.uniform(0.1, 0.5, n)
            mu = media * np.exp(0.12 * df[f"Exp_{mercado}_general"])
            df[f"target_{mercado}_total"] = rng.negative_binomial(
                10, 10 / (10 + mu),
            ).astype(float)
            df.loc[0, f"Exp_{mercado}_rol"] = np.nan
        # La API de features conserva también Remates aunque no se modele.
        df["Match_CV_Remates"] = rng.uniform(0.1, 0.5, n)
        bloques.append(df)
    return pd.concat(bloques, ignore_index=True)


class ModeloH1Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dataset = crear_dataset()
        cls.ejecucion = ejecutar_baseline_h1(cls.dataset)

    def test_corte_orden_y_no_mutacion(self):
        datos = self.dataset.sample(frac=1, random_state=8)
        copia = datos.copy(deep=True)
        particion = dividir_temporalmente_h1(datos)
        pd.testing.assert_frame_equal(datos, copia)
        self.assertLess(particion.train.Fecha_hora_utc.max(),
                        particion.val.Fecha_hora_utc.min())
        self.assertLess(particion.val.Fecha_hora_utc.max(),
                        particion.test.Fecha_hora_utc.min())
        ids = []
        for split, temporada in TEMPORADAS_H1.items():
            df = getattr(particion, split)
            self.assertEqual(df.Temporada.unique().tolist(), [temporada])
            pd.testing.assert_frame_equal(
                df, df.sort_values(["Fecha_hora_utc", "Id_partido"]),
            )
            ids.append(set(df.Id_partido))
        self.assertFalse(ids[0] & ids[1] or ids[0] & ids[2] or ids[1] & ids[2])

    def test_rechaza_solapamientos_incluso_fechas_iguales(self):
        for temporada in ("25/26", "26/27"):
            datos = self.dataset.copy()
            anterior = "24/25" if temporada == "25/26" else "25/26"
            fecha = datos.loc[
                datos.Temporada.eq(anterior), "Fecha_hora_utc",
            ].max()
            indice = datos.index[datos.Temporada.eq(temporada)][0]
            datos.loc[indice, "Fecha_hora_utc"] = fecha
            with self.assertRaisesRegex(AssertionError, "RNF-07"):
                dividir_temporalmente_h1(datos)

    def test_rechaza_split_ausente_ids_y_temporadas_invalidas(self):
        with self.assertRaisesRegex(ValueError, "no vacíos"):
            dividir_temporalmente_h1(
                self.dataset.query("Temporada != '26/27'")
            )
        for columna, valor in (("Id_partido", 1), ("Fecha_hora_utc", pd.NaT),
                               ("Temporada", "27/28")):
            datos = self.dataset.copy()
            datos.loc[0, columna] = valor
            with self.subTest(columna=columna), self.assertRaises(ValueError):
                dividir_temporalmente_h1(datos)

    def test_umbrales_y_escaladores_solo_train(self):
        datos = self.dataset.copy()
        futuro = datos.Temporada.ne("24/25")
        columnas = list(dict.fromkeys(
            c for m in MERCADOS_H1 for c in predictoras_h1(m)
        ))
        datos.loc[futuro, columnas] += 1000
        datos.loc[futuro, "target_Corners_total"] += 500
        with patch("ml_models.h1.model.ajustar_umbrales_cv_h1",
                   wraps=ajustar_umbrales_cv_h1) as ajustar:
            particion = dividir_temporalmente_h1(datos)
        ajustar.assert_called_once()
        self.assertEqual(ajustar.call_args.args[0].Temporada.unique().tolist(),
                         ["24/25"])
        self.assertEqual(ajustar.call_args.kwargs, {"percentil": 0.75})
        self.assertEqual(particion.umbrales_cv,
                         self.ejecucion.particion.umbrales_cv)
        modelos = entrenar_modelos_h1(particion.train, "Corners")
        train = preparar_mercado_h1(particion.train, "Corners")
        x = train[predictoras_h1("Corners")].to_numpy()
        for nombre in ("Poisson", "BinomialNegativa"):
            modelo = modelos[nombre]
            np.testing.assert_allclose(modelo.escalador_.mean_, x.mean(axis=0))
            np.testing.assert_allclose(modelo.escalador_.scale_, x.std(axis=0))
            self.assertEqual(modelo.escalador_.n_samples_seen_, len(x))
            np.testing.assert_array_equal(
                modelo.beta_, self.ejecucion.modelos["Corners"][nombre].beta_,
            )
            antes = modelo.escalador_.mean_.copy()
            modelo.predict(x[:4] + 1)
            np.testing.assert_array_equal(antes, modelo.escalador_.mean_)
        self.assertEqual(modelos["NaiveMedia"].media_,
                         train.target_Corners_total.mean())

    def test_nulos_solo_del_mercado_sin_imputacion(self):
        df = self.ejecucion.particion.train.copy()
        df.loc[1, "target_Faltas_total"] = np.nan
        df.loc[2, "Exp_Corners_general"] = np.nan
        df.loc[3, "target_Corners_total"] = np.nan
        df.loc[4, "target_Corners_total"] = 0
        df.loc[5, "otra_columna"] = np.nan
        validos = preparar_mercado_h1(df, "Corners")
        self.assertEqual(len(validos), len(df) - 3)
        self.assertIn(1, validos.index)
        self.assertEqual(validos.loc[4, "target_Corners_total"], 0)
        self.assertTrue(validos.otra_columna.isna().all())
        for columna, valor in (("Exp_Corners_rol", np.inf),
                               ("target_Corners_total", -1),
                               ("target_Corners_total", 2.5)):
            malo = df.copy()
            malo.loc[6, columna] = valor
            with self.assertRaises(ValueError):
                preparar_mercado_h1(malo, "Corners")

    def test_probabilidades_acotadas_monotonas_y_formula(self):
        for mercado, modelos in self.ejecucion.modelos.items():
            df = preparar_mercado_h1(self.ejecucion.particion.test, mercado)
            x = df[predictoras_h1(mercado)].to_numpy()
            lineas = LINEAS_BINARIAS_H1[mercado]
            for modelo in modelos.values():
                p = modelo.predict_proba_over(x, lineas)
                self.assertTrue(np.isfinite(p).all())
                self.assertTrue(((p >= 0) & (p <= 1)).all())
                self.assertTrue((np.diff(p, axis=1) <= 0).all())
        mu = np.array([0, 2, 10, 50, 1000.0])
        for alpha in (0.0, 0.2):
            p = probabilidades_over_h1(mu, (9.5, 10.5, 11.5), alpha)
            dist = (stats.poisson(mu[:, None]) if not alpha else
                    stats.nbinom(1 / alpha, 1 / (1 + alpha * mu[:, None])))
            np.testing.assert_allclose(
                p, 1 - dist.cdf([9, 10, 11]), atol=1e-14,
            )

    def test_limite_poisson_explicito_y_ajuste_equidisperso(self):
        mu = np.linspace(0, 50, 100)
        esperado = probabilidades_over_h1(mu, (9.5, 10.5, 11.5))
        for alpha in (0, 1e-12, ALPHA_POISSON, 1.01e-6):
            np.testing.assert_allclose(
                probabilidades_over_h1(mu, (9.5, 10.5, 11.5), alpha),
                esperado, atol=1e-3, rtol=0,
            )
        # Cuantiles de Poisson: muestra determinista casi equidispersa.
        y = stats.poisson.ppf((np.arange(5000) + 0.5) / 5000, 10)
        x = np.zeros((len(y), 2))
        poisson = ModeloPoissonH1().fit(x, y)
        nb = ModeloBinomialNegativaH1().fit(x, y)
        self.assertLessEqual(nb.alpha_, ALPHA_POISSON)
        np.testing.assert_allclose(
            nb.predict_proba_over(x[:3], (9.5, 10.5, 11.5)),
            poisson.predict_proba_over(x[:3], (9.5, 10.5, 11.5)),
            atol=1e-3, rtol=0,
        )

    def test_recupera_sobredispersion_y_senal_de_conteos(self):
        rng = np.random.default_rng(2026)
        x = rng.normal(size=(4000, 1))
        mu = np.exp(2.3 + 0.2 * x[:, 0])
        y = rng.negative_binomial(4, 4 / (4 + mu))
        nb = ModeloBinomialNegativaH1().fit(x, y)
        self.assertAlmostEqual(nb.alpha_, 0.25, delta=0.04)
        self.assertAlmostEqual(nb.beta_[1] / nb.escalador_.scale_[0],
                               0.2, delta=0.04)
        poisson = ModeloPoissonH1().fit(x, y)
        log_nb = stats.nbinom.logpmf(
            y, 1 / nb.alpha_, 1 / (1 + nb.alpha_ * nb.predict(x)),
        ).sum()
        self.assertGreater(
            log_nb, stats.poisson.logpmf(y, poisson.predict(x)).sum(),
        )

    def test_poisson_mle_intercepto_y_ceros(self):
        x = np.ones((20, 2))
        y = np.arange(20)
        modelo = ModeloPoissonH1().fit(x, y)
        np.testing.assert_allclose(modelo.predict(x), y.mean(), atol=1e-7)
        for clase in (NaiveMedia, ModeloPoissonH1, ModeloBinomialNegativaH1):
            modelo = clase().fit(x, np.zeros(20))
            np.testing.assert_array_equal(modelo.predict(x), 0)
            np.testing.assert_array_equal(
                modelo.predict_proba_over(x, [9.5]), 0,
            )
            with self.assertRaises(ValueError):
                clase().fit(x[:0], y[:0])

    def test_segmentos_cobertura_y_metricas_ponderadas(self):
        tabla = self.ejecucion.resultados
        self.assertEqual(len(tabla), 162)
        for _, grupo in tabla.groupby(["Split", "Mercado", "Modelo", "Linea"]):
            g = grupo.set_index("Segmento")
            todos = g.loc["Todos"]
            partes = g.loc[["Elegibles_H1", "No_elegibles_H1"]]
            self.assertEqual(todos.N_partidos, partes.N_partidos.sum())
            self.assertAlmostEqual(partes.Cobertura_pct.sum(), 100)
            for metrica in (
                "MAE_conteo", "Accuracy", "Log_Loss", "Brier_Score",
            ):
                ponderada = np.average(
                    partes[metrica], weights=partes.N_partidos,
                )
                self.assertAlmostEqual(todos[metrica], ponderada)

    def test_metricas_con_oraculo_manual_y_umbral_inclusivo(self):
        class ModeloFijo:
            nombre = "Fijo"

            def predict(self, x):
                return np.array([9, 13])

            def predict_proba_over(self, x, lineas):
                return np.tile(np.array([0.5, 0.2])[:, None], (1, len(lineas)))

        df = preparar_mercado_h1(
            self.ejecucion.particion.val, "Corners",
        ).iloc[:2].copy()
        df["target_Corners_total"] = [8, 12]
        df["flag_elegible_h1_Corners"] = [True, False]
        tabla = evaluar_modelo_h1(ModeloFijo(), df, "Corners", "val_25_26")
        fila = tabla.iloc[0]
        self.assertEqual(fila.N_partidos, 2)
        self.assertEqual(fila.MAE_conteo, 1)
        self.assertEqual(fila.RMSE_conteo, 1)
        self.assertEqual(fila.Accuracy, 0)
        self.assertAlmostEqual(fila.Log_Loss, -(np.log(0.5) + np.log(0.2)) / 2)
        self.assertAlmostEqual(fila.Brier_Score, (0.5**2 + 0.8**2) / 2)
        self.assertEqual(fila.Tasa_real_over, 0.5)

    def test_segmento_vacio_y_split_sin_validos(self):
        df = self.ejecucion.particion.val.copy()
        df["flag_elegible_h1_Corners"] = True
        modelo = self.ejecucion.modelos["Corners"]["Poisson"]
        tabla = evaluar_modelo_h1(modelo, df, "Corners", "val_25_26")
        vacio = tabla.loc[tabla.Segmento.eq("No_elegibles_H1")]
        self.assertTrue(vacio.N_partidos.eq(0).all())
        self.assertTrue(vacio.Cobertura_pct.eq(0).all())
        self.assertTrue(vacio[list(METRICAS)].isna().all().all())
        df["target_Corners_total"] = np.nan
        tabla = evaluar_modelo_h1(modelo, df, "Corners", "val_25_26")
        self.assertTrue(tabla.N_partidos.eq(0).all())
        self.assertTrue(tabla.Cobertura_pct.isna().all())

    @unittest.skipUnless(DB_PATH.is_file(), "No existe database/oraculo.db")
    def test_humo_pipeline_y_sha256_solo_lectura(self):
        def huellas():
            resultado = {}
            for sufijo in ("", "-wal", "-shm", "-journal"):
                ruta = Path(str(DB_PATH) + sufijo)
                if ruta.exists():
                    with ruta.open("rb") as archivo:
                        digest = hashlib.file_digest(
                            archivo, "sha256",
                        ).hexdigest()
                    resultado[sufijo] = (digest, ruta.stat().st_mtime_ns)
            return resultado

        antes = huellas()
        try:
            resultado = ejecutar_baseline_h1()
            self.assertEqual(len(resultado.resultados), 162)
            self.assertTrue(resultado.resultados.N_partidos.gt(0).all())
            self.assertTrue(
                np.isfinite(resultado.resultados[list(METRICAS)]).all().all()
            )
        finally:
            self.assertEqual(antes, huellas())


if __name__ == "__main__":
    unittest.main()
