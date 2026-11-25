"""Dataset prepartido H1: historia desplazada, targets y filtro por CV.

Uso desde la raíz: python -m ml_models.h1.features
La CLI muestra un resumen con umbrales ajustados en el primer 80 % temporal.
La API no ajusta umbrales automáticamente: el consumidor entrega solo train a
ajustar_umbrales_cv_h1 y reutiliza el resultado en validación/test.

Las ventanas describen una evaluación secuencial: un resultado observado puede
informar encuentros posteriores, incluso dentro de test. No son pronósticos
simultáneos de todo un horizonte con historia congelada. Los únicos valores
del encuentro actual que salen del módulo son los targets, siempre al final.
El logger hereda la configuración central de utils/logger.py; este módulo no
crea handlers ni archivos al importar o ejecutar su resumen de solo lectura.
"""

import logging
from pathlib import Path

import numpy as np
import pandas as pd

from ml_models.analisis_volumen import (
    METRICAS,
    conectar_solo_lectura,
    limpiar_equipo,
)


LOGGER = logging.getLogger(__name__)
MERCADOS = ("Corners", "Saques_de_banda", "Faltas", "Remates")
CONTEXTO = ("Posesion_balon", "Goles_esperados_xG")
LINEAS = {
    "Corners": (9.5, 10.5, 11.5),
    "Saques_de_banda": (33.5, 34.5, 35.5),
    "Faltas": (21.5, 22.5, 23.5),
    "Remates": (23.5, 24.5, 25.5),
}
METADATOS = [
    "Id_partido", "Id_liga", "Nombre_liga", "Temporada", "Ronda",
    "Fecha_hora_utc",
]
COLUMNAS_BASE = [
    *METADATOS, "Id_equipo", "Nombre_equipo", "Condicion_local", "Periodo",
    *MERCADOS, *CONTEXTO,
]
SQL_BASE_H1 = f"""
SELECT p.Id_partido, p.Id_liga, l.Nombre_liga, l.Temporada, p.Ronda,
       p.Fecha_hora_utc, pe.Id_equipo, e.Nombre_equipo, pe.Condicion_local,
       'ALL' AS Periodo,
       {', '.join('s.' + m for m in (*MERCADOS, *CONTEXTO))}
FROM PARTIDOS p
JOIN LIGAS l ON l.Id_liga = p.Id_liga
JOIN PARTIDOS_EQUIPOS pe ON pe.Id_partido = p.Id_partido
JOIN EQUIPOS e ON e.Id_equipo = pe.Id_equipo
LEFT JOIN PARTIDOS_ESTADISTICAS s
  ON s.Id_partido = pe.Id_partido AND s.Id_equipo = pe.Id_equipo
 AND (CASE WHEN s.Periodo = '2ND' THEN '2ST' ELSE s.Periodo END) = 'ALL'
"""


def _preparar_base(datos: pd.DataFrame) -> pd.DataFrame:
    """Valida pares y cronología; conserva estadísticas ausentes como NaN."""
    faltantes = set(COLUMNAS_BASE) - set(datos.columns)
    if faltantes or datos.columns.duplicated().any():
        raise ValueError(
            f"Columnas faltantes o duplicadas: {sorted(faltantes)}"
        )
    base = datos.loc[:, COLUMNAS_BASE].copy()
    base["Periodo"] = base["Periodo"].replace({"2ND": "2ST"})
    base = base.loc[base["Periodo"].eq("ALL")].reset_index(drop=True)
    # Reutiliza las reglas del EDA para conteos inválidos y fechas UTC.
    base, incidencias = limpiar_equipo(base.reindex(columns=[
        *base.columns, *[m for m in METRICAS if m not in base.columns],
    ]))
    for incidencia in incidencias.to_dict("records"):
        LOGGER.warning(
            "H1: Id_partido=%s Id_equipo=%s métrica=%s inválida; se usa NaN",
            incidencia["Id_partido"], incidencia["Id_equipo"],
            incidencia["Metrica"],
        )
    base = base.loc[:, COLUMNAS_BASE]
    claves = ["Id_partido", "Id_liga", "Id_equipo", "Fecha_hora_utc"]
    invalidas = base[claves].isna().any(axis=1)
    invalidas |= ~base["Condicion_local"].isin([0, 1])
    invalidas |= base.duplicated(["Id_partido", "Id_equipo"], keep=False)
    if invalidas.any():
        ids = base.loc[invalidas, "Id_partido"].tolist()
        raise ValueError(
            f"Claves, fecha o condición inválidas: partidos {ids}"
        )
    partidos = base.groupby("Id_partido", sort=False)
    pares = (
        partidos.size().eq(2)
        & partidos["Condicion_local"].nunique().eq(2)
        & partidos["Id_equipo"].nunique().eq(2)
        & partidos[METADATOS[1:]].nunique(dropna=False).eq(1).all(axis=1)
    )
    if not pares.all():
        raise ValueError(
            f"Pares o metadatos inconsistentes: partidos {pares[~pares].index}"
        )
    simultaneas = base.duplicated(
        ["Id_liga", "Id_equipo", "Fecha_hora_utc"], keep=False
    )
    if simultaneas.any():
        ids = base.loc[simultaneas, "Id_partido"].tolist()
        raise ValueError(f"Cronología ambigua para un equipo: partidos {ids}")
    base = base.sort_values([
        "Id_liga", "Id_equipo", "Fecha_hora_utc", "Id_partido",
    ]).reset_index(drop=True)
    rival = base[["Id_partido", "Condicion_local", *MERCADOS]].copy()
    rival["Condicion_local"] = 1 - rival["Condicion_local"]
    rival = rival.rename(columns={m: f"{m}_contra" for m in MERCADOS})
    base = base.merge(
        rival, on=["Id_partido", "Condicion_local"], validate="one_to_one",
        sort=False,
    ).rename(columns={m: f"{m}_favor" for m in MERCADOS})
    for mercado in MERCADOS:
        base[f"{mercado}_partido"] = (
            base[f"{mercado}_favor"] + base[f"{mercado}_contra"]
        )
    return base


def _calcular_historia(base: pd.DataFrame) -> pd.DataFrame:
    """Desplaza dentro de cada grupo antes de cualquier ventana móvil."""
    grupos = ["Id_liga", "Id_equipo"]
    general = base.groupby(grupos, sort=False)
    por_rol = base.groupby([*grupos, "Condicion_local"], sort=False)
    features = {}
    for mercado in MERCADOS:
        for sentido in ("favor", "contra", "partido"):
            columna = f"{mercado}_{sentido}"
            for ventana, minimo in ((5, 3), (10, 5)):
                features[f"{columna}_mean_{ventana}"] = general[
                    columna
                ].transform(
                    lambda s: s.shift(1).rolling(ventana, minimo).mean()
                )
            features[f"{columna}_rol_mean_5"] = por_rol[columna].transform(
                lambda s: s.shift(1).rolling(5, min_periods=3).mean()
            )
            features[f"{columna}_std_10"] = general[columna].transform(
                lambda s: s.shift(1).rolling(10, min_periods=5).std(ddof=1)
            )
        media = features[f"{mercado}_partido_mean_10"]
        features[f"{mercado}_partido_cv_10"] = (
            features[f"{mercado}_partido_std_10"] / media.where(media.ne(0))
        )
    for columna in CONTEXTO:
        features[f"{columna}_mean_10"] = general[columna].transform(
            lambda s: s.shift(1).rolling(10, min_periods=5).mean()
        )
    return pd.DataFrame(features, index=base.index)


def construir_dataset_h1(
    datos_equipo: pd.DataFrame | None = None,
    raiz: str | Path | None = None,
) -> pd.DataFrame:
    """Devuelve una fila por partido, sin ajustar umbrales ni imputar nulos.

    Sin datos_equipo consulta SQLite mediante mode=ro y query_only=ON. Para
    pruebas acepta filas equipo-partido-período ya cruzadas (COLUMNAS_BASE).
    Cada partido ALL debe tener ambos participantes; estadísticas ausentes se
    representan como NaN. Fechas inválidas o simultáneas para un mismo equipo
    se rechazan porque no permiten establecer historia estrictamente previa.
    Id_liga identifica la edición de liga, incluida su temporada, en SQLite.
    """
    LOGGER.info("H1: inicio de construcción del dataset prepartido")
    if datos_equipo is None:
        with conectar_solo_lectura(raiz) as conexion:
            datos_equipo = pd.read_sql_query(SQL_BASE_H1, conexion)
    base = _preparar_base(datos_equipo)
    historia = _calcular_historia(base)
    lados = []
    roles = ((1, "L_", "local"), (0, "V_", "visita"))
    for condicion, prefijo, nombre in roles:
        mascara = base["Condicion_local"].eq(condicion)
        columnas = METADATOS if condicion else ["Id_partido"]
        lado = base.loc[mascara, [
            *columnas, "Id_equipo", "Nombre_equipo",
        ]].rename(columns={
            "Id_equipo": f"Id_equipo_{nombre}",
            "Nombre_equipo": f"Equipo_{nombre}",
        })
        lados.append(pd.concat([
            lado, historia.loc[mascara].add_prefix(prefijo),
        ], axis=1))
    resultado = lados[0].merge(
        lados[1], on="Id_partido", validate="one_to_one"
    ).sort_values(["Fecha_hora_utc", "Id_partido"]).reset_index(drop=True)
    cruces = {}
    targets = {}
    reales = base.loc[base["Condicion_local"].eq(1)].set_index("Id_partido")
    for mercado in MERCADOS:
        for tipo, sufijo in (("general", "mean_10"), ("rol", "rol_mean_5")):
            local = (
                resultado[f"L_{mercado}_favor_{sufijo}"]
                + resultado[f"V_{mercado}_contra_{sufijo}"]
            ) / 2
            visita = (
                resultado[f"V_{mercado}_favor_{sufijo}"]
                + resultado[f"L_{mercado}_contra_{sufijo}"]
            ) / 2
            cruces[f"Exp_{mercado}_{tipo}"] = local + visita
            if tipo == "general":
                cruces[f"Diff_{mercado}_general"] = local - visita
        cruces[f"Match_CV_{mercado}"] = (
            resultado[f"L_{mercado}_partido_cv_10"]
            + resultado[f"V_{mercado}_partido_cv_10"]
        ) / 2
        total = resultado["Id_partido"].map(reales[f"{mercado}_partido"])
        targets[f"target_{mercado}_total"] = total
        for linea in LINEAS[mercado]:
            etiqueta = str(linea).replace(".", "_")
            targets[f"target_{mercado}_over_{etiqueta}"] = (
                total.gt(linea).astype(float).where(total.notna())
            )
    metadata = [*METADATOS, "Id_equipo_local", "Equipo_local",
                "Id_equipo_visita", "Equipo_visita"]
    features = [c for c in resultado.columns if c not in metadata]
    resultado = pd.concat([
        resultado[metadata + features],
        pd.DataFrame(cruces, index=resultado.index),
        pd.DataFrame(targets, index=resultado.index),
    ], axis=1)
    LOGGER.info(
        "H1: dataset construido, filas=%s columnas=%s", *resultado.shape
    )
    return resultado


def ajustar_umbrales_cv_h1(
    df_train: pd.DataFrame, percentil: float = 0.75,
) -> dict[str, float]:
    """Ajusta solo con train; un mercado sin CV válido devuelve umbral NaN."""
    if not 0 <= percentil <= 1:
        raise ValueError("percentil debe estar entre 0 y 1")
    return {
        mercado: float(df_train[f"Match_CV_{mercado}"].quantile(percentil))
        for mercado in MERCADOS
    }


def aplicar_filtro_elegibilidad_h1(
    df: pd.DataFrame, umbrales_cv: dict[str, float],
) -> pd.DataFrame:
    """Aplica umbrales fijos sin recalcularlos ni modificar el DataFrame."""
    faltantes = set(MERCADOS) - set(umbrales_cv)
    if faltantes:
        raise ValueError(f"Faltan umbrales para {sorted(faltantes)}")
    resultado = df.copy()
    for mercado in MERCADOS:
        cv = resultado[f"Match_CV_{mercado}"]
        resultado[f"flag_elegible_h1_{mercado}"] = (
            cv.notna() & cv.le(umbrales_cv[mercado])
        ).fillna(False).astype(bool)
    targets = [c for c in resultado if c.startswith("target_")]
    entradas = [c for c in resultado if c not in targets]
    return resultado[entradas + targets]


def main() -> None:
    """Resumen de diagnóstico en consola; no guarda datasets ni modelos."""
    dataset = construir_dataset_h1()
    if dataset.empty:
        print(f"Dimensiones del dataset: {dataset.shape}")
        return
    corte = dataset.iloc[int(len(dataset) * 0.8)]["Fecha_hora_utc"]
    es_train = dataset["Fecha_hora_utc"].lt(corte)
    umbrales = ajustar_umbrales_cv_h1(dataset.loc[es_train])
    filtrado = aplicar_filtro_elegibilidad_h1(dataset, umbrales)
    print(f"Dimensiones: base={dataset.shape}, con flags={filtrado.shape}")
    print(f"Columnas duplicadas: {dataset.columns.duplicated().sum()}")
    print(f"Train: {es_train.sum()} filas anteriores a {corte}")
    print(f"Test secuencial: {(~es_train).sum()} filas desde el corte")
    resumen = pd.DataFrame({
        "Umbral_CV_train": umbrales,
        "Elegibles_total_pct": {
            m: 100 * filtrado[f"flag_elegible_h1_{m}"].mean()
            for m in MERCADOS
        },
        "Elegibles_test_pct": {
            m: 100 * filtrado.loc[~es_train, f"flag_elegible_h1_{m}"].mean()
            for m in MERCADOS
        },
    })
    print(resumen.to_string(float_format=lambda x: f"{x:.4f}"))
    columnas = [
        "Id_partido", "Fecha_hora_utc", "Equipo_local", "Equipo_visita",
        "L_Corners_favor_mean_10", "V_Corners_contra_mean_10",
        "Exp_Corners_general", "Match_CV_Corners",
        "flag_elegible_h1_Corners", "target_Corners_total",
    ]
    print(filtrado[columnas].tail(5).to_string(index=False))


if __name__ == "__main__":
    main()
