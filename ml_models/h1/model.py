"""Baseline H1 de conteos y evaluación temporal, sin escrituras en SQLite.

Ejecutar desde la raíz: python -m ml_models.h1.model
SciPy ajusta máxima verosimilitud; no se requieren sklearn ni statsmodels.
El filtro H1 segmenta la evaluación: todos los modelos usan el mismo train.
"""

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import optimize, stats

from ml_models.h1.features import (
    LINEAS,
    ajustar_umbrales_cv_h1,
    aplicar_filtro_elegibilidad_h1,
    construir_dataset_h1,
)


MERCADOS_H1 = ("Corners", "Saques_de_banda", "Faltas")
LINEAS_BINARIAS_H1 = {m: LINEAS[m] for m in MERCADOS_H1}
TEMPORADAS_H1 = {"train": "24/25", "val": "25/26", "test": "26/27"}
SPLITS_EVALUACION = {"val": "val_25_26", "test": "test_26_27"}
ALPHA_POISSON = 1e-6
METRICAS = (
    "MAE_conteo", "RMSE_conteo", "Accuracy", "Log_Loss",
    "Brier_Score", "Tasa_real_over",
)


def predictoras_h1(mercado: str) -> list[str]:
    """Lista cerrada de ocho entradas históricas; nunca incluye targets."""
    if mercado not in MERCADOS_H1:
        raise ValueError(f"Mercado H1 no admitido: {mercado}")
    return [
        f"Exp_{mercado}_general", f"Exp_{mercado}_rol",
        f"Diff_{mercado}_general", f"Match_CV_{mercado}",
        "L_Posesion_balon_mean_10", "V_Posesion_balon_mean_10",
        "L_Goles_esperados_xG_mean_10", "V_Goles_esperados_xG_mean_10",
    ]


@dataclass
class ParticionH1:
    """Splits ordenados con flags y umbrales aprendidos solo de train."""

    train: pd.DataFrame
    val: pd.DataFrame
    test: pd.DataFrame
    umbrales_cv: dict[str, float]


def dividir_temporalmente_h1(
    dataset: pd.DataFrame | None = None,
    raiz: str | Path | None = None,
) -> ParticionH1:
    """Separa temporadas exactas y exige tres intervalos no vacíos disjuntos.

    Rechaza temporadas desconocidas, IDs repetidos y fechas inválidas. Ajusta
    el percentil 75 antes de descartar nulos específicos de cada mercado.
    El DataFrame de entrada no se modifica.
    """
    datos = construir_dataset_h1(raiz=raiz) if dataset is None else dataset
    datos = datos.copy()
    ids = datos["Id_partido"]
    if ids.isna().any() or ids.duplicated().any():
        raise ValueError("Id_partido debe ser único y no nulo")
    if not datos["Temporada"].isin(TEMPORADAS_H1.values()).all():
        raise ValueError("Temporadas admitidas: 24/25, 25/26 y 26/27")
    datos["Fecha_hora_utc"] = pd.to_datetime(
        datos["Fecha_hora_utc"], utc=True, errors="raise", format="mixed",
    )
    if datos["Fecha_hora_utc"].isna().any():
        raise ValueError("Fecha_hora_utc no puede contener nulos")
    datos = datos.sort_values(["Fecha_hora_utc", "Id_partido"])
    splits = {
        nombre: datos.loc[datos.Temporada.eq(temporada)].copy()
        for nombre, temporada in TEMPORADAS_H1.items()
    }
    if any(df.empty for df in splits.values()):
        raise ValueError("Se requieren train, val y test no vacíos")
    train, val, test = (splits[s] for s in TEMPORADAS_H1)
    limites_validos = (
        train.Fecha_hora_utc.max() < val.Fecha_hora_utc.min()
        and val.Fecha_hora_utc.max() < test.Fecha_hora_utc.min()
    )
    if not limites_validos:
        raise AssertionError("RNF-07: las temporadas se solapan temporalmente")
    assert train.Fecha_hora_utc.max() < val.Fecha_hora_utc.min()
    assert val.Fecha_hora_utc.max() < test.Fecha_hora_utc.min()
    umbrales = ajustar_umbrales_cv_h1(train, percentil=0.75)
    return ParticionH1(**{
        nombre: aplicar_filtro_elegibilidad_h1(df, umbrales)
        for nombre, df in splits.items()
    }, umbrales_cv=umbrales)


def preparar_mercado_h1(df: pd.DataFrame, mercado: str) -> pd.DataFrame:
    """Descarta solo NaN de las ocho entradas o del target de este mercado."""
    columnas = predictoras_h1(mercado) + [f"target_{mercado}_total"]
    validos = df.dropna(subset=columnas).copy()
    valores = validos[columnas].to_numpy(dtype=float)
    if not np.isfinite(valores).all():
        raise ValueError(f"Valores no finitos en {mercado}")
    y = validos[columnas[-1]].to_numpy(dtype=float)
    if np.any((y < 0) | (y != np.floor(y))):
        raise ValueError("El target debe ser un conteo entero no negativo")
    return validos


@dataclass
class EscaladorH1:
    """Equivalente numérico a StandardScaler (ddof=0; constantes: escala 1)."""

    mean_: np.ndarray
    scale_: np.ndarray
    n_samples_seen_: int

    @classmethod
    def ajustar(cls, x: np.ndarray) -> "EscaladorH1":
        escala = x.std(axis=0, ddof=0)
        return cls(x.mean(axis=0), np.where(escala > 0, escala, 1.0), len(x))

    def transformar(self, x: np.ndarray) -> np.ndarray:
        return (x - self.mean_) / self.scale_


def probabilidades_over_h1(mu, lineas, alpha: float = 0.0) -> np.ndarray:
    """Matriz partido × línea: SF(floor(L)), estable también si alpha→0.

    NB2: Var(Y|X)=mu+alpha*mu², n=1/alpha, p=1/(1+alpha*mu).
    SF evita la cancelación de 1-CDF en colas pequeñas.
    """
    mu = np.asarray(mu, dtype=float).reshape(-1, 1)
    lineas = np.asarray(lineas, dtype=float).reshape(1, -1)
    if (not np.isfinite(mu).all() or np.any(mu < 0)
            or not np.isfinite(lineas).all()
            or not np.isfinite(alpha) or alpha < 0):
        raise ValueError("Medias, líneas o dispersión inválidas")
    if alpha <= ALPHA_POISSON:
        return stats.poisson.sf(np.floor(lineas), mu)
    return stats.nbinom.sf(np.floor(lineas), 1 / alpha, 1 / (1 + alpha * mu))


def _validar_xy(x, y=None):
    x = np.asarray(x, dtype=float)
    if x.ndim != 2 or not np.isfinite(x).all():
        raise ValueError("X debe ser una matriz finita sin nulos")
    if y is None:
        return x
    y = np.asarray(y, dtype=float)
    if (y.ndim != 1 or len(y) != len(x) or not len(y)
            or not np.isfinite(y).all()
            or np.any((y < 0) | (y != np.floor(y)))):
        raise ValueError("Train debe contener X e y válidos y no vacíos")
    return x, y


def _ajustar_beta(x, y, inicio, alpha=0.0):
    """Optimiza la log-verosimilitud media con gradiente analítico."""
    def objetivo(beta):
        eta = x @ beta
        with np.errstate(over="ignore", invalid="ignore"):
            mu = np.exp(eta)
        if not np.isfinite(mu).all():
            return np.inf, np.zeros_like(beta)
        if alpha == 0:
            # La constante log(y!) no afecta al óptimo.
            perdida = np.mean(mu - y * eta)
        else:
            perdida = -stats.nbinom.logpmf(
                y, 1 / alpha, 1 / (1 + alpha * mu),
            ).mean()
        gradiente = x.T @ ((mu - y) / (1 + alpha * mu)) / len(y)
        return perdida, gradiente

    ajuste = optimize.minimize(
        objetivo, inicio, jac=True, method="BFGS",
        options={"gtol": 1e-7, "maxiter": 1000},
    )
    # BFGS puede informar pérdida de precisión con gradiente ya convergido.
    if (not np.isfinite(ajuste.fun)
            or np.max(np.abs(ajuste.jac)) > 1e-5):
        raise RuntimeError(
            f"No converge la regresión de conteos: {ajuste.message}"
        )
    return ajuste.x


class NaiveMedia:
    """Poisson con media del target válido de train, sin usar features."""

    nombre = "NaiveMedia"
    alpha_ = 0.0

    def fit(self, x, y):
        x, y = _validar_xy(x, y)
        self.media_ = float(y.mean())
        self.n_features_in_ = x.shape[1]
        return self

    def predict(self, x):
        x = _validar_xy(x)
        if x.shape[1] != self.n_features_in_:
            raise ValueError("Número de predictoras incompatible")
        return np.full(len(x), self.media_)

    def predict_proba_over(self, x, lineas):
        return probabilidades_over_h1(self.predict(x), lineas, self.alpha_)


class ModeloPoissonH1(NaiveMedia):
    """GLM con intercepto, enlace log y MLE sin penalización."""

    nombre = "Poisson"

    def fit(self, x, y):
        x, y = _validar_xy(x, y)
        super().fit(x, y)
        self.escalador_ = EscaladorH1.ajustar(x)
        diseno = np.column_stack([np.ones(len(x)),
                                  self.escalador_.transformar(x)])
        self.beta_ = np.zeros(diseno.shape[1])
        self.alpha_ = 0.0
        self.limite_cero_ = self.media_ == 0
        if not self.limite_cero_:
            self.beta_[0] = np.log(self.media_)
            self.beta_ = _ajustar_beta(diseno, y, self.beta_)
        return self

    def predict(self, x):
        x = _validar_xy(x)
        if x.shape[1] != self.n_features_in_:
            raise ValueError("Número de predictoras incompatible")
        if self.limite_cero_:
            return np.zeros(len(x))
        eta = self.beta_[0] + self.escalador_.transformar(x) @ self.beta_[1:]
        with np.errstate(over="ignore"):
            mu = np.exp(eta)
        if not np.isfinite(mu).all():
            raise ValueError("Predicción no finita; revisar extrapolación")
        return mu


class ModeloBinomialNegativaH1(ModeloPoissonH1):
    """NB2 con alpha estimado por verosimilitud perfilada solo en train.

    Se optimiza beta para cada alpha y se compara con el límite Poisson.
    alpha_=0 representa explícitamente ese límite (incluido train todo cero).
    """

    nombre = "BinomialNegativa"

    def fit(self, x, y):
        x, y = _validar_xy(x, y)
        super().fit(x, y)
        if self.limite_cero_:
            return self
        diseno = np.column_stack([np.ones(len(x)),
                                  self.escalador_.transformar(x)])
        beta_poisson = self.beta_.copy()
        mu = self.predict(x)
        perdida_poisson = -stats.poisson.logpmf(y, mu).mean()

        def perfil(log_alpha):
            alpha = float(np.exp(log_alpha))
            beta = _ajustar_beta(diseno, y, beta_poisson, alpha)
            medias = np.exp(diseno @ beta)
            return -stats.nbinom.logpmf(
                y, 1 / alpha, 1 / (1 + alpha * medias),
            ).mean()

        # Amplía el intervalo hasta encerrar el mínimo, sin fijar un techo
        # estadístico a alpha. El extremo inferior usa el límite Poisson.
        superior = 0.0
        anterior, actual = perfil(superior - 1), perfil(superior)
        while actual < anterior:
            superior += 1
            anterior, actual = actual, perfil(superior)
            if superior > 20:
                raise RuntimeError("No se logra acotar la dispersión NB2")
        ajuste = optimize.minimize_scalar(
            perfil, bounds=(np.log(ALPHA_POISSON), superior),
            method="bounded", options={"xatol": 1e-6},
        )
        if not ajuste.success or not np.isfinite(ajuste.fun):
            raise RuntimeError("No converge el perfil de dispersión NB2")
        alpha = float(np.exp(ajuste.x))
        if (alpha > ALPHA_POISSON * 1.01
                and ajuste.fun < perdida_poisson - 1e-8):
            self.alpha_ = alpha
            self.beta_ = _ajustar_beta(diseno, y, beta_poisson, alpha)
        return self


def entrenar_modelos_h1(df_train: pd.DataFrame, mercado: str) -> dict:
    """Ajusta los tres modelos sobre exactamente las mismas filas válidas."""
    train = preparar_mercado_h1(df_train, mercado)
    x = train[predictoras_h1(mercado)].to_numpy(dtype=float)
    y = train[f"target_{mercado}_total"].to_numpy(dtype=float)
    return {
        clase.nombre: clase().fit(x, y)
        for clase in (NaiveMedia, ModeloPoissonH1, ModeloBinomialNegativaH1)
    }


def evaluar_modelo_h1(modelo, df, mercado: str, split: str) -> pd.DataFrame:
    """Nueve filas por modelo/split; cobertura sobre válidos del mercado.

    Un segmento vacío tiene N=0, cobertura 0 y métricas NaN. Si el split no
    tiene ninguna fila válida, también su cobertura es NaN (0/0).
    """
    if split not in SPLITS_EVALUACION.values():
        raise ValueError("Split de evaluación no admitido")
    validos = preparar_mercado_h1(df, mercado)
    x = validos[predictoras_h1(mercado)].to_numpy(dtype=float)
    y = validos[f"target_{mercado}_total"].to_numpy(dtype=float)
    mu = modelo.predict(x)
    lineas = LINEAS_BINARIAS_H1[mercado]
    probabilidades = modelo.predict_proba_over(x, lineas)
    flag = validos[f"flag_elegible_h1_{mercado}"]
    if flag.isna().any() or not flag.isin([True, False]).all():
        raise ValueError("Elegibilidad debe ser booleana y no nula")
    elegibles = flag.to_numpy(dtype=bool)
    segmentos = {"Todos": np.ones(len(y), dtype=bool),
                 "Elegibles_H1": elegibles, "No_elegibles_H1": ~elegibles}
    filas = []
    for segmento, mascara in segmentos.items():
        n = int(mascara.sum())
        for j, linea in enumerate(lineas):
            metricas = dict.fromkeys(METRICAS, np.nan)
            if n:
                real = (y[mascara] > linea).astype(float)
                p = probabilidades[mascara, j]
                seguro = np.clip(p, 1e-15, 1 - 1e-15)
                error = mu[mascara] - y[mascara]
                metricas = {
                    "MAE_conteo": float(np.abs(error).mean()),
                    "RMSE_conteo": float(np.sqrt(np.mean(error ** 2))),
                    "Accuracy": float(np.mean((p >= 0.5) == real)),
                    "Log_Loss": float(-np.mean(
                        real * np.log(seguro) + (1 - real) * np.log1p(-seguro)
                    )),
                    "Brier_Score": float(np.mean((p - real) ** 2)),
                    "Tasa_real_over": float(real.mean()),
                }
            filas.append({
                "Split": split, "Mercado": mercado, "Modelo": modelo.nombre,
                "Segmento": segmento, "Linea": linea, "N_partidos": n,
                "Cobertura_pct": 100 * n / len(y) if len(y) else np.nan,
                **metricas,
            })
    return pd.DataFrame(filas)


@dataclass
class ResultadoH1:
    """Artefactos en memoria para auditoría, notebook e inferencia."""

    particion: ParticionH1
    modelos: dict
    muestras: pd.DataFrame
    resultados: pd.DataFrame


def ejecutar_baseline_h1(dataset=None, raiz=None) -> ResultadoH1:
    """Construye, separa, ajusta en 24/25 y evalúa sin refits posteriores."""
    particion = dividir_temporalmente_h1(dataset, raiz)
    modelos, muestras, tablas = {}, [], []
    for mercado in MERCADOS_H1:
        modelos[mercado] = entrenar_modelos_h1(particion.train, mercado)
        for split, temporada in TEMPORADAS_H1.items():
            df = getattr(particion, split)
            validos = preparar_mercado_h1(df, mercado)
            y = validos[f"target_{mercado}_total"]
            muestras.append({
                "Temporada": temporada, "Mercado": mercado,
                "N_antes": len(df), "N_validos": len(validos),
                "N_descartados_NaN": len(df) - len(validos),
                "Media_train": y.mean() if split == "train" else np.nan,
                "Var_Mean_train": (
                    y.var(ddof=1) / y.mean()
                    if split == "train" and y.mean() > 0 else np.nan
                ),
            })
            if split in SPLITS_EVALUACION:
                for modelo in modelos[mercado].values():
                    tablas.append(evaluar_modelo_h1(
                        modelo, validos, mercado, SPLITS_EVALUACION[split],
                    ))
    return ResultadoH1(particion, modelos, pd.DataFrame(muestras),
                       pd.concat(tablas, ignore_index=True))


def resumir_resultados_h1(tabla: pd.DataFrame) -> pd.DataFrame:
    """Promedio macro de las tres líneas; N no suma partidos repetidos."""
    return tabla.groupby(
        ["Split", "Mercado", "Modelo", "Segmento"], sort=False,
    ).agg(N_partidos=("N_partidos", "first"),
          Cobertura_pct=("Cobertura_pct", "first"),
          **{m: (m, "mean") for m in METRICAS}).reset_index()


def main() -> None:
    """Imprime muestras y tablas; no guarda archivos ni configura handlers."""
    ejecucion = ejecutar_baseline_h1()
    formato = lambda x: f"{x:.4f}"
    print("Muestras por temporada y mercado (ALL):")
    print(ejecucion.muestras.to_string(index=False, float_format=formato))
    resumen = resumir_resultados_h1(ejecucion.resultados)
    for split in SPLITS_EVALUACION.values():
        print(f"\n{split}: promedio macro de las tres líneas por mercado")
        print(resumen.loc[resumen.Split.eq(split)].drop(columns="Split")
              .to_string(index=False, float_format=formato))


if __name__ == "__main__":
    main()
