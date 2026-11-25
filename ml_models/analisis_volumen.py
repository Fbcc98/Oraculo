"""Herramientas descriptivas reutilizables; SQLite es la única fuente de datos.

No escribe en SQLite ni imputa ausencias como ceros. Las funciones estadísticas
aceptan DataFrames para facilitar nuevas exploraciones y pruebas aisladas.
"""

from contextlib import contextmanager
from pathlib import Path
import sqlite3

import numpy as np
import pandas as pd
from scipy import stats


PERIODOS = ("ALL", "1ST", "2ST")
MERCADOS = ("Corners", "Faltas", "Saques_de_banda", "Remates")
CONTEOS = MERCADOS + (
    "Tiros_arco", "Tiros_bloqueados", "Tarjetas_amarillas", "Tarjetas_rojas",
    "Tiros_libres", "Fueras_de_juego", "Saques_de_arco", "Total_centros",
    "Entradas", "Total_entradas",
)
METRICAS = CONTEOS + ("Posesion_balon", "Goles_esperados_xG")
ESQUEMA = {
    "PAIS": "Id_pais Codigo_alpha3 Nombre_pais".split(),
    "LIGAS": "Id_liga Id_pais Id_temporada_externo Nombre_liga Temporada".split(),
    "EQUIPOS": "Id_equipo Id_pais Nombre_equipo Slug".split(),
    "PARTIDOS": (
        "Id_partido Id_liga Ronda Goles_local Goles_visita "
        "Alineacion_confirmada Fecha_hora_utc Url"
    ).split(),
    "PARTIDOS_EQUIPOS": "Id_partido Id_equipo Condicion_local Formacion".split(),
    "PARTIDOS_ESTADISTICAS": ["Id_partido", "Id_equipo", "Periodo", *METRICAS],
}

# LEFT JOIN mantiene equipos sin estadísticas; la cuadrícula incorpora períodos
# ausentes. Esas filas son oportunidades esperadas, no observaciones imputadas.
SQL_EQUIPO_PERIODO = f"""
WITH periodos(Periodo) AS (VALUES ('ALL'), ('1ST'), ('2ST'))
SELECT p.Id_partido, p.Id_liga, l.Id_pais, l.Nombre_liga, l.Temporada,
       p.Ronda, p.Fecha_hora_utc, p.Goles_local, p.Goles_visita,
       pe.Id_equipo, e.Nombre_equipo, pe.Condicion_local, pe.Formacion,
       per.Periodo, s.Periodo AS Periodo_origen,
       (s.Id_partido IS NOT NULL) AS Tiene_estadisticas,
       {', '.join('s.' + m for m in METRICAS)}
FROM PARTIDOS p
JOIN LIGAS l ON l.Id_liga = p.Id_liga
JOIN PARTIDOS_EQUIPOS pe ON pe.Id_partido = p.Id_partido
JOIN EQUIPOS e ON e.Id_equipo = pe.Id_equipo
CROSS JOIN periodos per
LEFT JOIN PARTIDOS_ESTADISTICAS s
  ON s.Id_partido = pe.Id_partido AND s.Id_equipo = pe.Id_equipo
 AND (CASE WHEN s.Periodo = '2ND' THEN '2ST' ELSE s.Periodo END) = per.Periodo
ORDER BY p.Fecha_hora_utc, p.Id_partido, pe.Condicion_local DESC, per.Periodo
"""

# SQL de auditoría de totales crudos. COUNT(m)=2 evita que SUM(NULL, x)
# se convierta en un falso total. La versión limpia se construye en pandas.
SQL_TOTALES = f"""
WITH base AS ({SQL_EQUIPO_PERIODO})
SELECT Id_partido, Periodo, COUNT(*) AS N_equipos,
       {', '.join(f'CASE WHEN COUNT(*) = 2 AND COUNT(DISTINCT Condicion_local) = 2 AND COUNT({m}) = 2 THEN SUM({m}) END AS {m}' for m in CONTEOS)}
FROM base GROUP BY Id_partido, Periodo
"""


def encontrar_raiz(inicio=None):
    """Resuelve la raíz desde el proyecto o cualquier subdirectorio."""
    inicio = Path(inicio or Path.cwd()).resolve()
    for ruta in (inicio, *inicio.parents):
        if (ruta / "database").is_dir() and (ruta / "ml_models").is_dir():
            return ruta
    raise FileNotFoundError("No se encontró la raíz con database/ y ml_models/.")


@contextmanager
def conectar_solo_lectura(raiz=None):
    """Abre únicamente database/oraculo.db, nunca crea una base faltante."""
    db_path = encontrar_raiz(raiz) / "database" / "oraculo.db"
    if not db_path.is_file():
        raise FileNotFoundError(
            f"Falta {db_path}. Cargar SQLite con el ETL antes de ejecutar el EDA."
        )
    # as_uri escapa espacios y caracteres especiales y funciona en Windows/Linux.
    conexion = sqlite3.connect(f"{db_path.as_uri()}?mode=ro", uri=True)
    try:
        conexion.execute("PRAGMA query_only = ON")
        conexion.execute("BEGIN")  # Una única instantánea para todas las consultas.
        yield conexion
    finally:
        conexion.close()


def auditar(conexion):
    """Comprueba contrato, claves y cobertura sin cambiar esquema ni registros."""
    for tabla, columnas in ESQUEMA.items():
        presentes = {r[1] for r in conexion.execute(f'PRAGMA table_info("{tabla}")')}
        faltantes = set(columnas) - presentes
        if faltantes:
            raise ValueError(f"Esquema incompatible: {tabla}, faltan {sorted(faltantes)}")
    integridad = pd.read_sql_query("PRAGMA quick_check", conexion)
    foraneas = pd.read_sql_query("PRAGMA foreign_key_check", conexion)
    controles_sql = {
        "partidos_sin_dos_condiciones": """
            SELECT p.Id_partido FROM PARTIDOS p LEFT JOIN PARTIDOS_EQUIPOS pe
            ON pe.Id_partido=p.Id_partido GROUP BY p.Id_partido
            HAVING COUNT(pe.Id_equipo) != 2 OR COUNT(DISTINCT pe.Condicion_local) != 2
                OR MIN(pe.Condicion_local) != 0 OR MAX(pe.Condicion_local) != 1""",
        "estadisticas_duplicadas": """
            SELECT Id_partido, Id_equipo,
              CASE WHEN Periodo='2ND' THEN '2ST' ELSE Periodo END AS Periodo_canonico
            FROM PARTIDOS_ESTADISTICAS
            GROUP BY Id_partido, Id_equipo, Periodo_canonico HAVING COUNT(*) > 1""",
        "periodos_no_admitidos": """
            SELECT DISTINCT Periodo FROM PARTIDOS_ESTADISTICAS
            WHERE Periodo NOT IN ('ALL','1ST','2ST','2ND') OR Periodo IS NULL""",
    }
    controles = {k: pd.read_sql_query(sql, conexion) for k, sql in controles_sql.items()}
    if integridad.iloc[:, 0].tolist() != ["ok"] or not foraneas.empty:
        raise ValueError(f"Integridad SQLite fallida: {integridad}; claves: {foraneas}")
    for nombre, incidencias in controles.items():
        if not incidencias.empty:
            raise ValueError(f"Revisar {nombre}: {incidencias.head(10).to_dict('records')}")
    resumen = pd.read_sql_query("""
        SELECT (SELECT COUNT(*) FROM PAIS) AS Paises,
          (SELECT COUNT(*) FROM LIGAS) AS Ediciones_liga,
          (SELECT COUNT(*) FROM (SELECT DISTINCT Id_pais, Nombre_liga FROM LIGAS)) AS Ligas,
          (SELECT COUNT(DISTINCT Temporada) FROM LIGAS) AS Temporadas,
          (SELECT COUNT(*) FROM (SELECT DISTINCT Id_liga, Ronda FROM PARTIDOS
                                 WHERE Ronda IS NOT NULL)) AS Rondas_liga_temporada,
          (SELECT COUNT(*) FROM PARTIDOS) AS Partidos,
          (SELECT COUNT(*) FROM PARTIDOS_ESTADISTICAS) AS Filas_estadisticas
    """, conexion)
    cobertura = pd.read_sql_query("""
        SELECT l.Id_liga, l.Nombre_liga, l.Temporada, COUNT(p.Id_partido) AS Partidos,
          COUNT(DISTINCT p.Ronda) AS Rondas, MIN(p.Fecha_hora_utc) AS Desde_utc,
          MAX(p.Fecha_hora_utc) AS Hasta_utc
        FROM LIGAS l LEFT JOIN PARTIDOS p ON p.Id_liga=l.Id_liga
        GROUP BY l.Id_liga, l.Nombre_liga, l.Temporada
    """, conexion)
    # NULL SQL sobre filas existentes, separado de filas de períodos ausentes.
    nulos = pd.read_sql_query(f"""
        SELECT Periodo, COUNT(*) AS N_filas,
        {', '.join(f'100.0 * SUM(CASE WHEN {m} IS NULL THEN 1 ELSE 0 END) / NULLIF(COUNT(*),0) AS {m}' for m in METRICAS)}
        FROM PARTIDOS_ESTADISTICAS GROUP BY Periodo
    """, conexion)
    return {"resumen": resumen, "cobertura": cobertura, "nulos_sql_pct": nulos,
            "integridad": integridad, "claves_foraneas": foraneas}


def limpiar_equipo(datos):
    """Conserva ceros válidos; invalida conteos negativos/fraccionarios y texto."""
    limpio = datos.copy()
    incidencias = []
    for metrica in METRICAS:
        original = limpio[metrica]
        numeros = pd.to_numeric(original, errors="coerce").astype(float)
        invalido = numeros.notna() & (~np.isfinite(numeros) | numeros.lt(0))
        if metrica in CONTEOS:
            invalido |= numeros.notna() & numeros.mod(1).ne(0)
        if metrica == "Posesion_balon":
            invalido |= numeros.gt(100)
        invalido |= original.notna() & numeros.isna()
        for indice in limpio.index[invalido]:
            incidencias.append({
                **limpio.loc[indice, ["Id_partido", "Id_equipo", "Periodo"]].to_dict(),
                "Metrica": metrica, "Valor_original": original.loc[indice],
            })
        limpio[metrica] = numeros.mask(invalido)
    limpio["Fecha_hora_utc"] = pd.to_datetime(
        limpio["Fecha_hora_utc"], utc=True, errors="coerce", format="mixed"
    )
    limpio["Condicion"] = limpio["Condicion_local"].map({1: "Local", 0: "Visita"})
    return limpio, pd.DataFrame(incidencias, columns=[
        "Id_partido", "Id_equipo", "Periodo", "Metrica", "Valor_original"
    ])


def construir_totales(equipo):
    """Suma solo pares completos; posesión no se suma ni se usa como total."""
    claves = ["Id_partido", "Periodo"]
    metadata = ["Id_liga", "Id_pais", "Nombre_liga", "Temporada", "Ronda", "Fecha_hora_utc"]
    grupo = equipo.groupby(claves, dropna=False, observed=True)
    suma = grupo[list(CONTEOS) + ["Goles_esperados_xG"]].sum(min_count=2)
    par_valido = grupo.size().eq(2) & grupo["Condicion_local"].nunique().eq(2)
    suma.loc[~par_valido, :] = np.nan
    return grupo[metadata].first().join(suma).join(grupo.size().rename("N_equipos")).reset_index()


def describir(datos, grupos, metricas=MERCADOS):
    """SD muestral (ddof=1), IQR Q75-Q25 y CV=SD/media, sin porcentaje."""
    largo = datos.melt(id_vars=grupos, value_vars=list(metricas),
                       var_name="Mercado", value_name="Valor")
    tabla = largo.groupby([*grupos, "Mercado"], dropna=False, observed=True)["Valor"].agg(
        N="count", N_esperado="size", Media="mean", DE="std", Mediana="median",
        Q25=lambda s: s.quantile(.25), Q75=lambda s: s.quantile(.75),
        Asimetria="skew",
    ).reset_index()
    tabla["IQR"] = tabla["Q75"] - tabla["Q25"]
    tabla["CV"] = tabla["DE"].div(tabla["Media"].where(tabla["Media"].gt(0)))
    tabla["Cobertura_pct"] = 100 * tabla["N"] / tabla["N_esperado"]
    return tabla


def ranking_estabilidad(datos, grupos, min_n=30, min_cobertura=90):
    """Umbrales exploratorios configurables, no garantía de predictibilidad."""
    tabla = describir(datos, grupos)
    tabla["Elegible"] = (tabla.N.ge(min_n) & tabla.Cobertura_pct.ge(min_cobertura)
                         & tabla.CV.notna())
    tabla["Puesto"] = np.nan
    elegibles = tabla.loc[tabla.Elegible]
    tabla.loc[tabla.Elegible, "Puesto"] = elegibles.groupby(
        ["Periodo", "Mercado"], observed=True
    )["CV"].rank(method="min")
    return tabla.sort_values(["Periodo", "Mercado", "Puesto", "CV"], na_position="last")


def detectar_atipicos(datos, grupos, min_n=8):
    """Cercas de Tukey por mercado y estrato; marca, nunca elimina partidos."""
    ids = list(dict.fromkeys([*grupos, "Id_partido", "Id_equipo", "Nombre_equipo"]))
    largo = datos.melt(id_vars=ids, value_vars=list(MERCADOS),
                       var_name="Mercado", value_name="Valor")
    agrupado = largo.groupby([*grupos, "Mercado"], dropna=False, observed=True)["Valor"]
    largo["N_grupo"] = agrupado.transform("count")
    q25 = agrupado.transform(lambda s: s.quantile(.25))
    q75 = agrupado.transform(lambda s: s.quantile(.75))
    largo["Limite_inferior"] = q25 - 1.5 * (q75 - q25)
    largo["Limite_superior"] = q75 + 1.5 * (q75 - q25)
    largo["Atipico"] = largo.N_grupo.ge(min_n) & (
        largo.Valor.lt(largo.Limite_inferior) | largo.Valor.gt(largo.Limite_superior)
    )
    return largo


def ajustar_conteos(serie):
    """Poisson por media y NB por momentos; comparación descriptiva in-sample.

    NB: r=mu²/(s²-mu), p=mu/s², Var=mu+mu²/r. No se ajusta si s²<=mu.
    Log-verosimilitud no valida pronósticos y no es MLE para la NB.
    """
    x = pd.to_numeric(serie, errors="coerce").dropna().to_numpy(dtype=float)
    x = x[np.isfinite(x) & (x >= 0) & (x % 1 == 0)]
    resultado = dict(N=len(x), Media=np.nan, Varianza=np.nan, Razon_var_media=np.nan,
                     NB_r=np.nan, NB_p=np.nan, LogL_Poisson=np.nan, LogL_NB=np.nan,
                     Estado="Sin observaciones")
    if not len(x):
        return resultado
    mu = x.mean()
    var = x.var(ddof=1) if len(x) > 1 else np.nan
    resultado.update(Media=mu, Varianza=var, Razon_var_media=var / mu if mu > 0 else np.nan,
                     LogL_Poisson=float(stats.poisson.logpmf(x, mu).sum()),
                     Estado="NB no identificable: muestra insuficiente o sin sobredispersión")
    if len(x) >= 3 and mu > 0 and var > mu:
        r, p = mu**2 / (var - mu), mu / var
        resultado.update(NB_r=r, NB_p=p,
                         LogL_NB=float(stats.nbinom.logpmf(x, r, p).sum()),
                         Estado="Sobredispersión; NB por momentos")
    return resultado


def tabla_ajustes(datos, grupos=("Periodo",)):
    """Permite extender el ajuste por liga, temporada o condición."""
    filas = []
    for clave, bloque in datos.groupby(list(grupos), dropna=False, observed=True):
        clave = clave if isinstance(clave, tuple) else (clave,)
        for mercado in MERCADOS[:3]:
            filas.append({**dict(zip(grupos, clave)), "Mercado": mercado,
                          **ajustar_conteos(bloque[mercado])})
    return pd.DataFrame(filas)


def correlaciones(datos, periodo, min_n=30):
    """Spearman y tamaño pareado; variables del mismo partido son solo EDA."""
    bloque = datos.loc[datos.Periodo.eq(periodo), list(METRICAS)]
    correlacion = bloque.corr(method="spearman", min_periods=min_n)
    disponibles = bloque.notna().astype(int)
    n_pares = disponibles.T.dot(disponibles)
    return correlacion, n_pares
