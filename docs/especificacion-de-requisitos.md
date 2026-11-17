# Especificación de Requisitos

**Oráculo** es un sistema evolutivo orientado a identificar y operar *Value Bets* pre-partido en estadísticas de fútbol (principalmente mercados de volumen como córneres, faltas y saques de banda). El proyecto avanza por fases: inicia con la recolección histórica y analítica exploratoria en SQLite, continúa con el modelado predictivo y filtrado de cuotas, y condiciona la automatización de apuestas a la validación estadística previa de rentabilidad. Quedan excluidos el análisis en vivo (*in-play*) y el arbitraje multifuente (*surebets*).

---

## 1. Requisitos Funcionales (RF)

| ID | Nombre | Descripción | Fase |
| :--- | :--- | :--- | :--- |
| **RF-01** | **Crawling de URLs y Eventos** | Descubrimiento de enlaces de partidos y descarga de metadata general de encuentros por liga, temporada y ronda. | Fase 1 |
| **RF-02** | **Interceptación y Captura API** | Extracción de respuestas JSON (estadísticas, alineaciones y entrenadores) mediante Playwright y consultas autenticadas a endpoints. | Fase 1 |
| **RF-03** | **Pipeline ETL y Orquestación** | Limpieza, normalización y validación de entidades maestras y métricas cuantitativas desde JSON crudos, orquestado mediante CLI (`main.py`). | Fase 1 |
| **RF-04** | **Persistencia Relacional** | Carga transaccional de los datos normalizados en SQLite (`database/oraculo.db`) como fuente única de verdad. | Fase 1 |
| **RF-05** | **Dashboards Automatizados** | Generación de consultas y visualizaciones locales conectadas a SQLite para análisis descriptivo y definición de estrategias de mercado. | Fase 1 |
| **RF-06** | **Modelado Predictivo (ML)** | Entrenamiento y comparación de múltiples algoritmos para estimar probabilidades en eventos de volumen (córneres, faltas, saques de banda). | Fase 2 |
| **RF-07** | **Evaluación y Selección de Cuotas** | Captura de cuotas pre-partido y cruce automatizado con las probabilidades del modelo (apoyado por reglas matemáticas o IA) para identificar *Value Bets* ($EV > 0$). | Fase 2 |
| **RF-08** | **Ejecución Autónoma y Bitácora** | Colocación automatizada de apuestas sobre un *bankroll* designado (condicionada a superar la Fase 2) y registro automático de cada operación y resultado en SQLite para auditoría. | Fase 3 |

---

## 2. Requisitos No Funcionales (RNF)

| ID | Nombre | Descripción |
| :--- | :--- | :--- |
| **RNF-01** | **Comportamiento Humano** | Incorporación de pausas aleatorias (`random_sleep`) y manejo de sesiones de navegador para mitigar bloqueos anti-scraping[cite: 1, 3]. |
| **RNF-02** | **Parametrización Externa** | Configuración centralizada de ligas, temporadas, rondas y tiempos de espera mediante `config.json`, desacoplada del código fuente[cite: 3]. |
| **RNF-03** | **Portabilidad de Rutas** | Resolución dinámica de directorios mediante rutas relativas (`os.path` desde `BASE_DIR`) para ejecutar el sistema en distintos entornos sin editar código[cite: 1, 3]. |
| **RNF-04** | **Integridad Referencial y ACID** | Activación obligatoria de claves foráneas (`PRAGMA foreign_keys = ON`) y transacciones atómicas por partido en SQLite para evitar registros huérfanos[cite: 1, 3]. |
| **RNF-05** | **Idempotencia de Carga** | Capacidad de reejecutar el pipeline ETL sobre encuentros ya procesados sin duplicar registros mediante operaciones `UPSERT`[cite: 3]. |
| **RNF-06** | **Trazabilidad y Observabilidad** | Registro estructurado de eventos, advertencias y errores en consola y archivo de log (`oraculo_scraper.log`) identificando liga, ronda o partido afectado[cite: 3]. |
| **RNF-07** | **Validación Temporal (Sin *Data Leakage*)** | Los modelos predictivos deben entrenarse y evaluarse respetando estrictamente la cronología de los encuentros, exigiendo $\ge 60\%$ de acierto y $EV > 0$ antes de operar capital real. |
| **RNF-08** | **Control de Riesgo Financiero** | En fase operativa, el sistema debe aplicar reglas máximas de *stake* por apuesta y detención automática (*stop-loss*) ante desviaciones de rendimiento. |