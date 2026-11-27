# Estándares y Pruebas

Este documento establece las reglas de calidad de código, control de versiones y validación técnica del proyecto **Oráculo**. Dado que el sistema es una herramienta de uso personal construida en solitario con apoyo de Inteligencia Artificial (Codex / ChatGPT), estas normas definen el marco de referencia obligatorio para mantener el orden, asegurar la trazabilidad de cada cambio y evitar que la IA se salga de contexto o modifique componentes fuera de alcance.

---

## 1. Principios de Calidad de Software (ISO/IEC 25010)

El diseño y evolución del código se rigen por seis principios basados en la norma **ISO/IEC 25010** (enfocados en *Mantenibilidad* y *Analizabilidad*):

| Principio | Definición en Oráculo | Aplicación Práctica en el Código |
| :--- | :--- | :--- |
| **Modularidad** | Organizar el sistema en componentes independientes con responsabilidades únicas. | Separar estrictamente la navegación web (`scrapers/`), la normalización de datos (`etl/`), la persistencia SQL (`database/`) y la analítica (`ml_models/`). |
| **Escalabilidad** | Permitir incorporar nuevas ligas, métricas o modelos predictivos sin reescribir el núcleo. | Parametrizar ligas y rondas en `config.json` y utilizar mapeos declarativos (`ESTADISTICAS_SIMPLES`, `PLAYER_STATS_MAP`) en los procesadores. |
| **Mantenibilidad** | Reducir el costo y esfuerzo de ajustar el sistema cuando cambie la fuente externa (Sofascore). | Aislar selectores DOM y endpoints en funciones pequeñas dentro de `scrapers/` y centralizar conversiones de tipos en `etl/common.py`. |
| **Reutilización** | Evitar duplicación de lógica compartiendo utilidades comunes entre módulos. | Consumir `utils/logger.py`, `utils/json_reader.py`, `utils/base.py` y `etl/common.py` en lugar de reimplementar lecturas, pausas o sanitizaciones. |
| **Reportabilidad** | Emitir información transparente sobre cada operación para diagnosticar la raíz de cualquier fallo. | Registrar inicio, progreso, advertencias y errores con contexto (`Id_partido`, liga, ronda) mediante el logger compartido. |
| **Trazabilidad** | Vincular cada función, cambio y decisión con su documentación y tarea correspondiente. | Mantener actualizados los contratos en `/docs`, documentar *docstrings* claros y asociar cada rama de Git a un *Issue* de GitHub Projects. |

---

## 2. Convenciones de Código y Desarrollo Asistido por IA

### 2.1 Estilo y Aislamiento de Capas
* **Estilo Python (PEP 8):** Aplicar PEP 8 en todo código nuevo o refactorizado. Usar indentación de 4 espacios, funciones y variables en `snake_case`, constantes en `MAYUSCULAS_CON_GUION_BAJO` y clases en `CapWords` (`PascalCase`).
* **Fronteras estrictas entre módulos:**
  * Ningún módulo en `scrapers/` debe importar `sqlite3` ni ejecutar consultas SQL.
  * Ninguna clase en `etl/` debe realizar peticiones HTTP ni interactuar con Playwright.
  * El módulo `ml_models/` lee exclusivamente desde `database/oraculo.db` en modo de solo lectura y nunca desde `data/raw/`.
* **Logging centralizado:** Utilizar exclusivamente `utils/logger.py` (`oraculo_scraper.log` y salida estándar) en lugar de `print()` para eventos operativos, incluyendo siempre el ID del encuentro o la jornada en mensajes de advertencia y error.

### 2.2 Reglas para Generación de Código con IA
* **Documentación como frontera de contexto:** Antes de solicitar código a una IA, se debe referenciar el documento correspondiente en `/docs` (especialmente `docs/arquitectura-del-sistema.md`) para respetar las firmas, rutas y tipos de datos existentes.
* **Prohibición de dependencias no acordadas:** No introducir librerías externas (como Pandas o SQLAlchemy en el ETL) si el contrato técnico establece el uso de estructuras nativas de Python y `sqlite3`.

---

## 3. Gestión de Repositorio y Flujo Git (Desarrollo en Solitario)

El control de versiones está diseñado para ofrecer seguridad y trazabilidad histórica sin burocracia innecesaria.

### 3.1 Ramas Permanentes
* **`master` (Producción / Estable):** Contiene únicamente versiones funcionales, probadas y documentadas del sistema. Está prohibido realizar *commits* directos sobre `master`.
* **`developer` (Integración y Pruebas):** Rama principal de desarrollo donde se integran y validan los cambios antes de promover una nueva versión estable hacia `master`.

### 3.2 Nomenclatura y Aislamiento de Ramas de Trabajo
Toda rama temporal nace desde `developer` y debe corresponder exactamente a una de las áreas definidas en las etiquetas (*labels*) de GitHub Projects: `scraping`, `etl`, `database`, `ml`, `docs`.

* **Formato obligatorio:**
  * Nueva funcionalidad: `feature/<area>-<nombre-de-la-funcionalidad>` (ej. `feature/etl-orquestador-main`, `feature/ml-modelo-corners`).
  * Refactorización o corrección de métodos: `hotfix/<area>-<nombre-de-la-funcionalidad>` (ej. `hotfix/scraping-idempotencia-partidos`).
* **Regla de aislamiento por área:** Cada rama debe crear o modificar únicamente archivos pertenecientes a su área declarada (por ejemplo, una rama `scraping` solo modifica archivos en `scrapers/`), salvo la actualización correspondiente en `/docs`.

### 3.3 Estructura de Commits
Los mensajes de *commit* deben ser concisos, descriptivos e incluir obligatoriamente el ámbito del módulo entre paréntesis, seguido de dos puntos y un espacio. Se admite uno de los siguientes tres formatos:

* `Feat(<modulo>): <descripción>` — Cuando se incorpora una nueva funcionalidad o módulo (ej. `Feat(ml_models): organizar subpaquete h1 de features`).
* `Fix(<modulo>): <descripción>` — Cuando se corrige un error o se refactoriza un método existente (ej. `Fix(ml_models): corregir ruta de la base en prueba de humo`).
* `Docs(<modulo>): <descripción>` — Cuando se crean o actualizan archivos de documentación (ej. `Docs(docs): documentar arquitectura ML y subpaquete h1`).

### 3.4 Pull Requests (Bitácora de Trazabilidad) y Checklist Pre-Merge
Aunque el desarrollo es en solitario y no requiere aprobación de terceros, toda integración hacia `developer` se realiza mediante **Pull Request (PR)** para dejar un registro visual de los cambios y vincular el cierre del *Issue* (`Closes #N`).

Antes de confirmar el *merge* de un PR hacia `developer`, se debe verificar este **checklist de 3 puntos**:
1. **Alcance limpio:** El *diff* modifica únicamente archivos del área indicada en el nombre de la rama (más `/docs` si aplica), sin alterar código no relacionado.
2. **Ejecución sin residuos:** El flujo afectado se ejecutó correctamente y no quedaron archivos temporales o bases de datos de prueba fuera de `.gitignore`.
3. **Sincronización documental:** Si cambió una entrada, salida, tabla o comando CLI, el cambio quedó reflejado en `/docs`.

Una vez validado un hito completo en `developer`, se realiza el *merge* de `developer` hacia `master`.

---

## 4. Estrategia de Pruebas y Criterios de Aceptación

### 4.1 Enfoque Pragmático de Validación
Al tratarse de un sistema de uso personal y no comercial, la estrategia de pruebas evita la sobre-ingeniería (como *mocks* complejos de navegador) y se enfoca en dos niveles prácticos:
* **Validación en ejecución real:** Todo cambio en `scrapers/` o `main.py` se considera válido cuando completa su ejecución de extremo a extremo sin excepciones no controladas y genera los artefactos esperados en `data/raw/` o SQLite.
* **Pruebas automatizadas asistidas por IA:** Para lógica crítica de transformación (`etl/`) y persistencia (`database/`), se apoyará en la IA para generar scripts rápidos de verificación sobre casos borde (valores nulos, porcentajes, claves duplicadas).
* **Protección de datos históricos:** Toda prueba experimental o automatizada debe ejecutarse contra una base de datos temporal (o en memoria `:memory:`), nunca directamente sobre la base de datos productiva `database/oraculo.db` sin respaldo previo, salvo la prueba de humo estrictamente de solo lectura descrita en la sección 4.3.

### 4.2 Matriz de Aceptación de SQLite (Carga Piloto)
Las pruebas de persistencia se ejecutan sobre un archivo SQLite temporal inicializado con `database/crear_db.py`, verificando que `PRAGMA foreign_keys = ON` esté activo en la conexión real utilizada por `Loader`.

| Prueba | Resultado Esperado |
| :--- | :--- |
| Consultar `PRAGMA foreign_keys` en la conexión activa | Devuelve `1`. |
| Cargar un partido válido completo | Las estadísticas apuntan al partido, equipo y período esperados. `PRAGMA foreign_key_check` devuelve cero filas. |
| Insertar una relación con un equipo inexistente | SQLite bloquea la operación y lanza `sqlite3.IntegrityError`. |
| Provocar un error de clave foránea al final de la carga | Se revierte la transacción completa (*rollback* atómico) sin dejar registros huérfanos. |
| Cargar dos veces el mismo encuentro (*idempotencia*) | Se conserva una única fila por clave primaria/compuesta y se actualizan los valores suministrados mediante `UPSERT`. |

Estos cinco casos definen la aceptación técnica de la **carga piloto** y su ejecución exitosa habilita el cierre del hito correspondiente en GitHub Projects.

### 4.3 Suite Unitaria de Machine Learning

Desde la raíz del proyecto, usando el entorno con sus dependencias instaladas:

```bash
python -m unittest discover -s ml_models -v
```

El descubrimiento incluye `ml_models/test_analisis_volumen.py` (5 pruebas), `ml_models/h1/test_features.py` (15 pruebas) y `ml_models/h1/test_model.py` (13 pruebas). Los archivos `__init__.py` de `ml_models/` y `ml_models/h1/` permiten organizar el paquete y descubrir sus pruebas. La aceptación de la instantánea actual exige 33 pruebas aprobadas, sin errores de importación ni omisiones cuando existe `database/oraculo.db`.

* **Cero fuga temporal (RNF-07):** Cambiar estadísticas reales del partido `t` no altera sus features de entrada ni las de partidos anteriores; solo puede afectar encuentros posteriores. Toda ventana aplica `.shift(1)` dentro del grupo correspondiente, respetando liga y rol local/visita.
* **Nulos y consistencia numérica:** Las ventanas insuficientes mantienen `NaN`; se verifican `min_periods`, `ddof=1`, CV con media cero, cruces entre rivales y targets con componentes ausentes. No se sustituyen ausencias por cero.
* **Separación train/test:** Los cuantiles de `Match_CV_{M}` se ajustan exclusivamente en train y se aplican a test como umbrales fijos, sin recalcularlos ni modificar el DataFrame original.
* **Baseline temporal H1:** Train `24/25`, validación `25/26` y test `26/27` deben formar intervalos estrictamente separados, incluso ante fechas de frontera iguales. Escaladores, media ingenua, coeficientes y dispersión se ajustan solo en train; cambios de features/targets futuros no modifican esos parámetros ni los umbrales.
* **Distribuciones y métricas:** Probabilidades acotadas y decrecientes al subir la línea; equivalencia NB/Poisson con tolerancia absoluta `1e-3` cerca de alpha cero; recuperación de sobredispersión sintética y MLE de intercepto. Se verifican métricas con valores calculados manualmente, suma de muestras/cobertura de segmentos, nulos específicos por mercado y segmentos vacíos.
* **Aislamiento de datos:** Las transformaciones H1 usan DataFrames sintéticos y SQLite en memoria; las pruebas descriptivas usan SQLite temporal. Ninguna prueba escribe sobre la base productiva.
* **Humo de solo lectura:** Si existe `database/oraculo.db`, se permite consultarla exclusivamente mediante la conexión centralizada de `analisis_volumen.py`. La prueba verifica URI `?mode=ro`, `PRAGMA query_only = ON`, 869 filas y 150 columnas sin duplicados, e igualdad de hash SHA-256, tamaño y fecha de modificación de la base y sus archivos auxiliares presentes antes/después. Si el archivo no existe, solo esta prueba se omite; las 869 filas corresponden a la instantánea de referencia, no a un límite del constructor.
* **Humo del modelo:** Ejecuta el pipeline completo sobre SQLite y comprueba 162 filas de resultados con métricas finitas en la instantánea actual, conservando hash SHA-256 y fecha de modificación de la base y auxiliares. Se omite, igual que el humo de features, únicamente cuando no existe la base. El notebook conserva todas sus celdas ejecutadas, gráficos y verificación SHA-256 antes/después; la selección del ganador utiliza solo validación.
