# Oráculo: Sistema Analítico y Pipeline ETL Deportivo

**Oráculo** busca ofrecer un respaldo financiero metódico y controlado para la familia mediante el análisis probabilístico de estadísticas de fútbol. A la par, funciona como un *sandbox* técnico para consolidar habilidades en ingeniería de datos, arquitectura de software y aprendizaje automático (*Machine Learning*).

---

## 1. Visión y Alcance

El sistema evoluciona en tres fases progresivas:
* **Objetivo Principal:** Extraer estadísticas históricas y pre-partido en SQLite como fuente única de verdad para alimentar dashboards locales de exploración (Fase 1), entrenar modelos predictivos que detecten *Value Bets* en mercados de volumen (córneres, faltas, saques de banda) con **$\ge 60\%$ de acierto y Valor Esperado positivo ($EV > 0$)** (Fase 2), y automatizar la ejecución sobre un *bankroll* designado con bitácora de auditoría una vez validada la rentabilidad (Fase 3).
* **Fuera del Alcance:** Queda estrictamente excluida la operación con dinero real sin validación previa de Fase 2, el análisis o apuestas en vivo (*in-play*), el arbitraje multifuente (*surebets*) y el desarrollo de aplicaciones web o móviles comerciales.

---

## 2. Arquitectura de Alto Nivel

1. **Extracción (`scrapers/`):** Playwright navega por Sofascore e intercepta respuestas de la API para guardar en JSON crudos los eventos de temporada, enlaces por jornada, estadísticas, alineaciones y entrenadores.
2. **Transformación (`etl/`):** Procesadores *stateless* en Python nativo (`MatchProcessor`, `PlayerProcessor`, `ManagerProcessor`) limpian, normalizan y estructuran los JSON sin dependencias pesadas.
3. **Carga y Orquestación (`database/` y `main.py`):** `Loader` persiste los registros en SQLite (`database/oraculo.db`) mediante transacciones atómicas e idempotentes (`UPSERT`), orquestadas desde `main.py` vía menú interactivo o comandos CLI.

```text
Oráculo/
├── main.py              # Orquestador CLI (menú interactivo y banderas --full, --etl, --init-db, --status)
├── config.json          # Parámetros de ligas, temporadas, rondas y tiempos de espera
├── requirements.txt     # Dependencias del entorno Python
├── scrapers/            # Crawling de URLs y descarga de JSON crudos
├── etl/                 # Normalización de datos y coordinación del pipeline
├── database/            # Esquema DDL (crear_db.py) y base de datos SQLite (oraculo.db)
├── ml_models/           # Experimentación, entrenamiento y evaluación de modelos (Fase 2)
├── utils/               # Logger centralizado, lector de configuración y utilidades
├── data/raw/            # Almacenamiento local de JSON crudos (ignorado en Git)
└── docs/                # Documentación técnica detallada (Spokes)
```

## 3. Guía de Operación rápida (Runbook)

Desde la raíz del proyecto, crea el entorno virtual:

```sh
python -m venv .venv
```

Actívalo con `.\.venv\Scripts\Activate.ps1` en PowerShell o con `source .venv/bin/activate` en Bash. Luego instala las dependencias y el navegador e inicia el menú:

```sh
python -m pip install -r requirements.txt
python -m playwright install chromium
python main.py
```

Para realizar una captura, revisa la liga, las temporadas y la ronda en `config.json`. Ejecuta la opción 1 para descubrir los partidos y la opción 2 para procesar el archivo de jornada generado.

## 4. Índice de Documentación Detallada

| Sección Estratégica          | Descripción                           | Documento de Referencia                            |
|------------------------------|---------------------------------------|----------------------------------------------------|
| Vision general del proyecto  | Vision, objetivos y alcance.          | [Vision](docs/vision.md)                           |
| Especificación de Requisitos | RF y RNF.                             | [Requisitos](docs/especificacion-de-requisitos.md) |
| Arquitectura del Sistema     | Módulos, flujo y responsabilidades.   | [Arquitectura](docs/arquitectura-del-sistema.md)   |
| Modelo de Datos              | Tablas, atributos y claves en SQLite. | [Modelo relacional](docs/modelo-de-datos.md)       |
| Roadmap y Gestión de Tareas  | MVP, carga piloto y siguientes hitos. | [Roadmap](docs/roadmap-y-gestion.md)               |
| Estándares y Pruebas         | Convenciones y pruebas de integridad. | [Calidad](docs/estandares-y-pruebas.md)            |
