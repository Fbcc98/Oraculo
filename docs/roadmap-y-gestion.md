# Roadmap y Gestión de Tareas

El desarrollo de **Oráculo** avanza bajo un enfoque iterativo, incremental y orientado al aprendizaje. Cada fase entrega un producto funcional que valida las hipótesis de la etapa siguiente antes de escalar en complejidad técnica o riesgo financiero.

---

## 1. Gestión en GitHub Projects (Flujo Flexible)

La planificación operativa se centraliza en el tablero **`Desarrollo de 'Oraculo'`** en GitHub Projects. Dado que es un proyecto de desarrollo individual y aprendizaje continuo sin plazos rígidos, la gestión se organiza por **objetivos** y no por fechas calendario:

### 1.1 Estructura de Organización
* **Milestones por Macro-Fase:** Agrupan los *Issues* necesarios para cumplir el objetivo de cada etapa (`Fase 1: Piloto y Estrategia`, `Fase 2: Laboratorio ML`, `Fase 3: Automatización`). No se mapearán todas las tareas desde el día uno; los *Issues* se irán desmenuzando a medida que avance el estudio de cada fase.
* **Milestone Transversal (`Mejoras Continuas y Aprendizaje`):** Espacio permanente para alojar ideas de refactorización, optimización del *scraping*, mejoras en la consola o experimentos técnicos que surjan en el camino.
* **Labels (Etiquetas):** Clasifican cada *Issue* por capa de código (`area: scraping`, `area: etl`, `area: database`, `area: ml`, `area: analytics`) y naturaleza (`tipo: feat`, `tipo: fix`, `tipo: tech-debt`, `tipo: docs`).
* **Flujo de Columnas:** `Backlog` $\rightarrow$ `Ready` (máx. 3 tareas) $\rightarrow$ `In progress` (máx. 2 tareas simultáneas) $\rightarrow$ `Done`.

### 1.2 Manejo de Ventanas de Mantenimiento entre Fases
Entre una fase y otra existirán pausas naturales destinadas al estudio, limpieza de deuda técnica y mejora de herramientas:
1. Mientras se ejecuta una fase principal, cualquier idea de mejora no bloqueante se guarda como *Issue* dentro del Milestone **`Mejoras Continuas y Aprendizaje`** en la columna `Backlog`.
2. Al cerrar una fase, se abre una ventana flexible para ejecutar estas mejoras sin presión de tiempo. Si el aprendizaje adquirido sugiere cambiar el enfoque técnico de la siguiente fase, se ajustan o descartan los *Issues* del `Backlog` antes de iniciar el nuevo Milestone.

---

## 2. Hito Actual · Carga Piloto (Inicio de Fase 1)

El primer paso verificable es validar de extremo a extremo que un encuentro real descargado en JSON locales se transforma y persiste correctamente en SQLite (`database/oraculo.db`).

| Tarea | Criterio de cierre | Estado |
| :--- | :--- | :--- |
| **Seleccionar un encuentro finalizado** | Los archivos de evento (`league_events`) y estadísticas (`matchs_stats`) corresponden al mismo `Id_partido`. | Pendiente |
| **Armar el contexto** | La liga y la temporada coinciden. Los dos IDs de equipo son distintos y coinciden con el local y el visitante de la fuente. | Pendiente |
| **Cargar y consultar** | Una consulta SQL recupera fecha UTC, marcador, ambos equipos y estadísticas por período (`ALL`, `1ST`, `2ST`). Si hay alineaciones, se conservan las formaciones disponibles. | Pendiente |
| **Repetir la carga (Idempotencia)** | Los conteos por clave permanecen estables tras ejecutar dos veces la carga y `PRAGMA foreign_key_check` devuelve cero incidencias. | Pendiente |

* **Evidencia de cierre:** Adjuntar en el *Issue* correspondiente el `Id_partido` probado y el resultado de las consultas de aceptación.
* **Continuidad inmediata:** Validar el flujo desde `main.py` y extender la descarga y carga hacia jornadas completas.

---

## 3. Hoja de Ruta por Fases

| Fase | Enfoque Principal | Criterio de Paso (*Phase Gate*) |
| :--- | :--- | :--- |
| **Fase 1: Piloto, Datos y Estrategia** | Estabilizar el *scraping* y SQLite para alimentar **dashboards automatizados** de análisis exploratorio y definir la estrategia de apuesta. | Base de datos poblada de forma estable, dashboards operativos y estrategia de mercado/variables definida por escrito. |
| **Fase 2: Laboratorio ML y Selección de Cuotas** | Implementar y comparar múltiples modelos de ML basados en las hipótesis de Fase 1 (evaluando apoyo de IA para filtrar cuotas) y simular resultados. | Al menos un modelo alcanza **$\ge 60\%$ de acierto** con **Valor Esperado positivo ($EV > 0$)** en validación temporal. |
| **Fase 3: Ejecución Autónoma y Bitácora** | Automatizar el flujo completo: *scraping* de casa de apuestas, cruce con predicciones, ejecución automática sobre el fondo designado y registro en bitácora. | *(Fase final operativa)* Controlado mediante límites estrictos de capital (*stop-loss*) y auditoría continua de resultados. |

### Detalle de Entregables por Fase

#### Fase 1 · Versión Piloto, Consumo Directo y Definición de Estrategia
* **Pipeline de Datos Operativo:** Ejecutar de forma confiable el *scraping* básico (`match_crawler.py` + `stats_scraper.py`) y la carga a SQLite mediante `main.py`.
* **Dashboards Automatizados (Exploración):** Conectar herramientas ligeras de visualización local (ej. Streamlit o Jupyter Notebooks parametrizados) directamente a `oraculo.db` para observar distribuciones, promedios y tendencias por liga/equipo.
* **Definición de Estrategia:** A partir de lo observado en los dashboards, establecer qué mercados de volumen ofrecen patrones más predecibles y bajo qué reglas estadísticas conviene operar.

#### Fase 2 · Modelado Predictivo Automatizado
* **Experimentación Multi-Modelo:** Traducir las estrategias definidas en Fase 1 en variables predictivas (*features*) y entrenar distintos algoritmos de clasificación/probabilidad para compararlos objetivamente.
* **Evaluación de Cuotas:** Explorar mecanismos automatizados (incluyendo modelos de IA o reglas de probabilidad implícita) para detectar qué cuotas del mercado ofrecen valor real sin requerir búsqueda manual prolongada.
* **Filtro de Seguridad (Umbral 60 % + $EV > 0$):** Ningún modelo pasará a operar dinero real si no demuestra al menos un **60 % de capacidad de acierto** sobre datos históricos no vistos y rentabilidad matemática frente a las cuotas reales.

#### Fase 3 · Automatización Total y Bitácora de Auditoría
* **Cruce Mercado vs. Modelo:** Implementar el *scraping* de cuotas pre-partido en la casa de apuestas seleccionada y cruzarlo automáticamente con las predicciones del modelo ganador de Fase 2.
* **Ejecución Autónoma sobre Fondo Designado:** Automatizar la colocación de apuestas respetando el *bankroll* asignado y reglas máximas de exposición por encuentro.
* **Bitácora Automatizada de Resultados:** El sistema debe registrar en SQLite cada apuesta realizada (fecha, partido, mercado, cuota, monto apostado, probabilidad estimada y resultado final) para auditar su rendimiento real y detener la operación si se desvía de lo esperado.

---

## 4. Ideas Futuras (Backlog de Exploración)

* Separar la identidad de la competición (`COMPETICIONES`) de sus ediciones anuales (`TEMPORADAS`).
* Evaluar el impacto de bajas y ausencias por partido cuando exista una fuente consistente.
* Incorporar alertas automáticas de rendimiento cuando la tasa de acierto real en Fase 3 caiga por debajo del umbral del 60 %.