# Oráculo · Estrategia inicial de mercados de volumen

Fecha de corte del análisis: **23 de noviembre de 2026** (America/Santiago).
Issue: **[Feature] Implementar exploración descriptiva y definir estrategia de mercado**.
Estado: base descriptiva para planificar el **Milestone 2 / Laboratorio ML**.

## 1. Alcance y decisión inicial

Priorizar la investigación de **saques de banda, faltas y córneres totales en ALL**.
Mantener remates como mercado secundario y como señal histórica candidata. Estudiar
córneres y saques de banda de primera y segunda mitad como extensiones; posponer
faltas por mitad hasta resolver su cobertura desigual entre temporadas.

La elección se fundamenta en cobertura, dispersión y posibilidad de construir
variables pre-partido. No implica rentabilidad, probabilidades calibradas ni
disponibilidad de estas líneas en una casa de apuestas. El análisis actual no
contiene cuotas y no permite calcular valor esperado económico.

## 2. Fuente, trazabilidad y auditoría

Fuente analítica exclusiva: `database/oraculo.db`. Tras autorización del usuario,
se ejecutaron `main.py --init-db` y `main.py --etl` con el código existente para
crear la base y cargar los archivos disponibles. No se editaron `database/crear_db.py`,
`etl/` ni `scrapers/`. La capa `ml_models/` no consume JSON crudos.

El notebook [eda_mercados_volumen.ipynb](../ml_models/eda_mercados_volumen.ipynb)
consulta SQLite con URI `mode=ro`, `PRAGMA query_only` y una instantánea de lectura.
Las funciones extensibles están en [analisis_volumen.py](../ml_models/analisis_volumen.py).
Los resultados siguientes proceden de esas consultas, no de ejemplos sintéticos.

| Edición cargada | Partidos | Rondas distintas | Desde UTC | Hasta UTC |
| :--- | ---: | ---: | :--- | :--- |
| Premier League 24/25 | 380 | 38 | 2024-08-16 19:00 | 2025-05-25 15:00 |
| Premier League 25/26 | 380 | 38 | 2025-08-15 19:00 | 2026-05-24 15:00 |
| Premier League 26/27 | 109 | 11 | 2026-08-21 19:00 | 2026-11-22 16:30 |
| **Total** | **869** | **87 por edición** | | |

Una competición, tres ediciones/temporadas y **5.214 filas equipo–partido–período**.
`PAIS` contiene 80 registros de catálogo; esto no significa 80 países con ligas
analizadas. La cobertura se mide sobre partidos cargados, no sobre un calendario
oficial externo. No se infiere que 26/27 esté completa.

`quick_check=ok`, sin violaciones de claves foráneas, sin duplicados de claves
analíticas ni partidos sin un local y un visitante. No se detectaron valores
inválidos en las métricas analizadas. Los períodos presentes cubren los 869 partidos.

**Diferencia entre contrato y datos:** la base guarda `2ND`; el EDA lo presenta
como `2ST` y conserva `Periodo_origen`. La auditoría de NULL SQL mantiene la etiqueta
original. La coexistencia de ambos códigos para un mismo equipo–partido detiene
la extracción, evitando duplicar filas. No se modifica el dato persistido.

| Mercado | NULL equipo ALL | NULL equipo 1ST | NULL equipo 2ND | Totales válidos ALL / 1ST / 2ST |
| :--- | ---: | ---: | ---: | :--- |
| Córneres | 0 % | 0 % | 0 % | 869 / 869 / 869 |
| Faltas | 0 % | 50,86 % | 50,86 % | 869 / 427 / 427 |
| Saques de banda | 0 % | 0 % | 0 % | 869 / 869 / 869 |
| Remates | 0 % | 0 % | 0 % | 869 / 869 / 869 |

Faltas por mitad: cobertura 0 % en 24/25, 83,68 % en 25/26 y 100 % en 26/27.
La ausencia es dependiente de la temporada: no tratarla como aleatoria ni rellenarla
con cero. En otras candidatas destacan NULL de tarjetas rojas (87,80 %), fueras de
juego (5,18 %), amarillas (3,80 %) y tiros bloqueados (0,23 %) en cada período.
Posesión, xG, tiros al arco, centros y entradas tienen cobertura completa.

No se encontraron diferencias entre ALL y la suma de mitades en los cuatro mercados
cuando los tres valores existen: 869 partidos comparables por mercado, excepto
faltas, con 427. El EDA conserva ALL original y no reconstruye valores ausentes.

## 3. Resultados descriptivos de totales

Cada observación es la suma local + visitante del mismo partido y período, solo
con dos valores válidos. DE muestral; IQR = Q75 − Q25; CV = DE/media como razón.

| Mercado | Período | N | Media | DE | Mediana | IQR | CV | Asimetría |
| :--- | :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Córneres | ALL | 869 | 10,039 | 3,354 | 10 | 4 | 0,334 | 0,216 |
| Córneres | 1ST | 869 | 4,739 | 2,331 | 5 | 3 | 0,492 | 0,527 |
| Córneres | 2ST | 869 | 5,300 | 2,402 | 5 | 3 | 0,453 | 0,573 |
| Faltas | ALL | 869 | 22,074 | 5,156 | 22 | 8 | 0,234 | 0,214 |
| Faltas | 1ST | 427 | 10,630 | 3,041 | 10 | 4 | 0,286 | 0,273 |
| Faltas | 2ST | 427 | 11,356 | 3,538 | 11 | 5 | 0,312 | 0,221 |
| Saques de banda | ALL | 869 | 34,419 | 7,551 | 34 | 11 | 0,219 | 0,152 |
| Saques de banda | 1ST | 869 | 16,969 | 4,913 | 17 | 7 | 0,290 | 0,401 |
| Saques de banda | 2ST | 869 | 17,450 | 4,885 | 17 | 7 | 0,280 | 0,242 |
| Remates | ALL | 869 | 25,715 | 5,741 | 25 | 7 | 0,223 | 0,366 |
| Remates | 1ST | 869 | 11,763 | 3,603 | 12 | 5 | 0,306 | 0,384 |
| Remates | 2ST | 869 | 13,952 | 4,148 | 14 | 6 | 0,297 | 0,388 |

Entre los tres mercados prioritarios, saques de banda tiene el menor CV global
en ALL. La comparación es orientativa: la media, escala del conteo, mezcla de
equipos y dependencia entre rivales afectan al CV.

| Mercado ALL | Media local | Media visita | Diferencia local − visita |
| :--- | ---: | ---: | ---: |
| Córneres | 5,353 | 4,686 | +0,667 |
| Faltas | 10,810 | 11,264 | −0,453 |
| Saques de banda | 17,618 | 16,801 | +0,817 |
| Remates | 13,928 | 11,787 | +2,140 |

Las diferencias son descriptivas y pareadas por partido; no se presentan como
efectos causales ni pruebas de significación independientes.

## 4. Mercados seleccionados y líneas objetivo de investigación

Regla reproducible inicial: centro = `floor(mediana) + 0,5`; rejilla centro − 1,
centro y centro + 1. Las tres líneas son semienteras y no generan devolución.
Se deben recalcular únicamente en entrenamiento en Fase 2. Las cifras actuales
usan toda la muestra del EDA y **no son resultados fuera de muestra**.

| Prioridad | Mercado total ALL | Líneas candidatas | Frecuencia histórica over, en el mismo orden | Estado |
| :--- | :--- | :--- | :--- | :--- |
| 1 | Saques de banda | 33,5 / 34,5 / 35,5 | 52,59 % / 48,22 % / 42,35 % | Investigar; comprobar oferta real |
| 2 | Faltas | 21,5 / 22,5 / 23,5 | 54,20 % / 44,65 % / 36,48 % | Investigar ALL |
| 3 | Córneres | 9,5 / 10,5 / 11,5 | 56,16 % / 44,53 % / 30,72 % | Baseline comparable |
| Secundaria | Remates | Pendiente de validación del mercado | No seleccionada | Feature y exploración |

El notebook incluye rejillas por mitad, pendientes de selección. No sustituir
cuotas por frecuencias retrospectivas ni buscar una línea por tasa de acierto
sin considerar su precio. Antes de comparar, verificar definición del mercado,
duración reglamentaria, descuento, prórroga, anulaciones y proveedor estadístico.

## 5. Estabilidad por edición y equipo

Criterio exploratorio configurable: **N >= 30 valores válidos**, cobertura >= 90 %,
media positiva y CV definido. Ordenar CV ascendente dentro del mismo mercado y
período. Estratificar por edición para evitar que una temporada domine a otra.
Los umbrales son reglas de investigación iniciales, no requisitos validados de
rentabilidad. Revisar sensibilidad a ventanas, rival y condición en Fase 2.

| Mercado ALL | Edición con menor CV | N | CV | Equipo–edición con menor CV | N | CV |
| :--- | :--- | ---: | ---: | :--- | ---: | ---: |
| Córneres | 25/26 | 380 | 0,327 | Aston Villa 25/26 | 38 | 0,406 |
| Faltas | 26/27, parcial | 109 | 0,214 | Bournemouth 24/25 | 38 | 0,229 |
| Saques de banda | 25/26 | 380 | 0,201 | Manchester City 24/25 | 38 | 0,209 |
| Remates | 26/27, parcial | 109 | 0,199 | Brighton & Hove Albion 25/26 | 38 | 0,275 |

Solo hay una competición; el ranking de ligas compara sus ediciones y no permite
elegir entre países o competiciones. Los equipos de 26/27 aún no alcanzan 30
partidos por edición. No aplicar automáticamente rankings retrospectivos a 26/27.
Los rankings de equipos combinan local y visita; al separarlos, el umbral puede
dejar pocos o ningún equipo elegible.

Los saques de banda ALL cambian de media 32,900 en 24/25 a 35,829 en 25/26 y
34,798 en 26/27. Esa variación obliga a evaluar deriva entre temporadas, aun
cuando el CV sea relativamente bajo.

Outliers con cercas de Tukey (1,5×IQR), por edición–período–condición y N >= 8:
en ALL se marcaron 29 observaciones de equipo en córneres, 10 en faltas, 10 en
saques de banda y 44 en remates, sobre 1.738 observaciones por mercado. Se
conservan; revisar caso a caso antes de considerarlos errores. No recortar extremos
usando información de validación o prueba.

## 6. Distribuciones y modelos base

Poisson: λ = media. Binomial negativa por momentos: r = μ²/(s²−μ), p = μ/s²,
solo cuando N >= 3, μ > 0 y s² > μ. Los ajustes se comparan con la distribución
empírica y log-verosimilitud dentro de muestra, sin declarar un ganador predictivo.

| Mercado ALL | Varianza/media | r NB | p NB | Lectura inicial |
| :--- | ---: | ---: | ---: | :--- |
| Córneres | 1,120 | 83,417 | 0,893 | Sobredispersión moderada |
| Faltas | 1,204 | 108,018 | 0,830 | Sobredispersión moderada |
| Saques de banda | 1,657 | 52,426 | 0,604 | Mayor sobredispersión observada |

Faltas 1ST tiene razón 0,870: no corresponde ajustar NB mediante esa fórmula.
No confundir la razón con una prueba formal de ajuste. La mezcla de equipos,
temporadas y contextos puede explicar dispersión. En Fase 2 comparar modelos
condicionales, calibración de colas over/under y desempeño temporal. No suponer
independencia de los conteos local y visita al construir una distribución total.

## 7. Variables candidatas sin fuga temporal

En el EDA ALL por equipo (N=1.738 pares), Spearman es 0,648 entre centros y córneres,
0,437 entre posesión y córneres, 0,692 entre xG y remates y 0,639 entre tiros al
arco y remates. Son asociaciones **del mismo partido**: sus valores actuales no
están disponibles pre-partido. Solo motivan transformaciones históricas.

| Familia / columnas SQLite | Feature propuesta para Fase 2 | Disponibilidad y control temporal |
| :--- | :--- | :--- |
| Corners, Faltas, Saques_de_banda, Remates | Media, mediana, DE y CV de últimos 5/10/20 encuentros; ventanas expansivas | Ordenar por equipo y UTC; excluir partido objetivo con shift(1); exigir historial conocido al corte |
| PARTIDOS_EQUIPOS + mercados del rival | Conteos históricos concedidos por el rival | Autounión por partido y condición opuesta; después aplicar desfase temporal |
| Condicion_local | Indicador local/visita y medias históricas por condición | Identidad del encuentro conocida antes del inicio; ventanas solo con encuentros anteriores |
| Posesion_balon | Media histórica de posesión del equipo y rival | Nunca posesión del encuentro objetivo; validar escala 0–100 |
| Goles_esperados_xG | Media histórica de xG a favor y en contra | Disponibilidad posterior de estadísticas; registrar fecha de captura en futura capa de features |
| Tiros_arco, Tiros_bloqueados, Total_centros | Intensidad ofensiva histórica y proporciones con denominador válido | Desfase; no rellenar denominadores ausentes o cero con razones ficticias |
| Entradas, Total_entradas, Faltas, Tiros_libres | Intensidad defensiva histórica | Revisar redundancia de Entradas/Total_entradas antes de seleccionar ambas |
| Tarjetas_amarillas, Tarjetas_rojas, Fueras_de_juego | Disciplina y ritmo históricos | Prioridad baja por NULL, especialmente rojas; ausencia no equivale a cero |
| Id_liga, Temporada, Ronda | Contexto de edición y jornada | Ronda no sustituye fecha UTC; codificaciones ajustadas solo en entrenamiento |
| Fecha_hora_utc | Días desde último partido del equipo/rival y congestión del calendario | Solo encuentros previos disponibles; este historial solo cubre una competición |
| Formacion, Alineacion_confirmada | Posible contexto de alineación pre-partido | No habilitar sin snapshot previo al corte: el estado actual no prueba disponibilidad histórica |
| Cuotas y reglas de liquidación | Probabilidad implícita, margen y EV | No disponibles en estas tablas; adquisición futura separada con timestamp pre-partido |

`shift(1)` por sí solo no garantiza causalidad temporal si hay partidos simultáneos,
reprogramaciones, resultados aún no publicados o correcciones posteriores. Exigir
`fecha_fin/disponibilidad < fecha_corte` cuando exista esa trazabilidad. El esquema
actual guarda inicio UTC, no publicación ni versiones: documentar esta limitación
y mantener la simulación retrospectiva como provisional hasta disponer de snapshots.

## 8. Reglas de negocio y gestión de riesgo pre-partido

1. Operación de investigación y simulación exclusivamente; mantener la exclusión
   de dinero real prevista en la visión del proyecto hasta validación de Fase 2.
2. Definir un corte pre-partido reproducible y congelar features, cuota, mercado,
   línea y reglas de liquidación en ese instante. Excluir cualquier dato posterior.
3. Abstenerse si falta cobertura, historial, identidad de participantes, cuota o
   definición comparable del mercado. No inferir disponibilidad a partir del EDA.
4. En simulación inicial, usar una unidad fija virtual por selección y como máximo
   una selección por encuentro para no multiplicar exposición por mercados
   correlacionados. Congelar límites antes de evaluar; no aumentarlos por pérdidas.
5. Para líneas semienteras y cuota decimal q, evaluar EV por unidad como
   `p*q - 1`, con p calibrada fuera de muestra. Las líneas con devolución requieren
   modelar también el push. Incluir margen, disponibilidad y cambios de precio.
6. Registrar selecciones y abstenciones, versión del modelo, probabilidad, cuota,
   resultado, unidades, exposición y drawdown. Un dato inconsistente, desajuste de
   reglas o deterioro de calibración pausa la simulación y abre revisión.
7. El objetivo del proyecto de >= 60 % de acierto y EV positivo requiere evidencia
   temporal y precio real; no es una consecuencia de un CV bajo ni se ha verificado
   con este notebook. Definir límites de capital solo en un hito posterior autorizado.

## 9. Plan de validación y condiciones para Milestone 2

Separar todos los equipos, mitades y mercados de un mismo partido dentro del
mismo bloque temporal. Evitar divisiones aleatorias de filas. Imputaciones,
escaladores, selección de features, líneas, outliers y calibración se ajustan
exclusivamente con entrenamiento. Evaluar con avance temporal y bloques por fecha.

24/25 y 25/26 permiten desarrollar validación temporal retrospectiva, y 26/27
permite estudiar deriva. **Todas estas temporadas fueron exploradas en este EDA**:
no llamar a 26/27 un test final intacto. Reservar un tramo futuro todavía no
observado y congelar reglas antes de abrirlo.

| Entregable / condición | Estado en este corte | Siguiente paso |
| :--- | :--- | :--- |
| Lectura SQLite, auditoría y DataFrames reproducibles | Implementado | Reejecutar después de cada carga |
| Descriptivos y distribuciones iniciales | Implementado | Comparar por ventanas temporales |
| Estrategia de mercados y rejillas | Provisional, documentada | Selección solo con entrenamiento |
| Faltas por mitad | Cobertura insuficiente para mezcla de temporadas | Resolver disponibilidad antes de incluir |
| Comparación entre competiciones | No disponible, una liga | Ampliar cobertura mediante pipeline existente |
| Features pre-partido y disponibilidad histórica | Diseño definido, no implementado | Construir capa temporal y snapshots |
| Cuotas históricas y liquidación comparable | No disponibles | Diseñar adquisición con trazabilidad |
| Calibración, EV, ROI e incertidumbre fuera de muestra | Pendientes | Backtest por bloques y evaluación prospectiva |

La base descriptiva permite comenzar el laboratorio; no certifica el cumplimiento
del hito de rentabilidad ni el paso a ejecución real.

## 10. Reproducción y verificación

Desde la raíz del proyecto y con la rama `ml_models/feature/analisis-descriptivo`:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m unittest ml_models.test_analisis_volumen -v
.\.venv\Scripts\python.exe -m nbconvert --to notebook --execute --inplace ml_models/eda_mercados_volumen.ipynb --ExecutePreprocessor.timeout=180
```

Jupyter requiere sockets locales para comunicarse con el kernel. Seleccionar el
intérprete del entorno `.venv`. La resolución de la base admite ejecutar desde
la raíz o desde `ml_models/`, sin rutas absolutas incrustadas. Si falta la base,
el notebook informa el requisito y no crea una base vacía.

Los tests usan SQLite temporal y cubren apertura de solo lectura, cierre de
conexiones, ausencia de base, sumas incompletas, ceros, períodos ausentes, alias
duplicados, conteos inválidos, muestras pequeñas y condiciones de ajuste NB.
Los outputs y gráficos de la ejecución real se conservan en el `.ipynb`.
