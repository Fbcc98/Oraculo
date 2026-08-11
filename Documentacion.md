# 1. Visión General del Proyecto

## 1.1 Propósito del Proyecto:

El proyecto "Oráculo" es una iniciativa de desarrollo de software destinada a la recolección, estructuración y análisis de estadísticas de fútbol. 
Su propósito central es construir una herramienta automatizada que facilite la toma de decisiones estratégicas y basadas en datos dentro del ámbito 
de las apuestas deportivas.

A nivel personal, este sistema tiene un doble valor fundamental:

* Valor Práctico y Emocional: Busca generar una fuente de ingresos adicional de manera metódica y controlada, con el fin de brindar apoyo 
económico a mi familia y seres queridos.

* Valor Educativo (Sandbox Técnico): Funciona como un entorno de pruebas real para consolidar y poner en práctica conocimientos avanzados 
en Ingeniería de Software, Arquitectura de Datos (Web Scraping y automatización con Playwright), Modelamiento de Bases de Datos (SQLite/SQL) y 
Ciencia de Datos (Machine Learning y análisis predictivo).

## 1.2 Alcance:

El alcance inicial del proyecto contempla el ciclo de vida completo de los datos (Pipeline ETL), dividido en tres grandes fases tecnológicas: 
automatización de extracción (Web Scraping), almacenamiento relacional y análisis predictivo (Machine Learning).

### 1. Dentro del Alcance:

1. **Extracción de Datos**: Desarrollo de un motor de web scraping capaz de extraer el historial estadístico de partidos de forma automatizada.
2. **Fuente Única de Verdad**: Los datos se obtendrán inicialmente de un único portal deportivo, seleccionando estratégicamente aquel 
cuyas métricas y tiempos de actualización se alineen con los modelos utilizados por las casas de apuestas.
3. **Arquitectura de Datos (ETL)**: Diseño e implementación de una Base de Datos Relacional para procesar, limpiar y almacenar las 
estadísticas extraídas, permitiendo la generación de consultas e indicadores propios.
4. **Modelo de Machine Learning**: En su fase final, el proyecto incluye el diseño y entrenamiento de un algoritmo predictivo para estimar 
las condiciones generales de un partido (específicamente estadísticas de volumen, como overs de córneres, faltas o saques de banda), 
sirviendo como apoyo para identificar apuestas de valor (Value Bets).

### 2. Fuera del Alcance:

Para acotar el desarrollo y evitar la expansión descontrolada del proyecto (*Scope Creep*), se establecen formalmente los siguientes límites:

1. **Automatización Transaccional:** No incluye la colocación automatizada de apuestas (*Auto-betting*) ni la integración con plataformas de pago/casinos.
2. **Frecuencia Temporal:** Exclusivamente pre-partido (*pre-match*). No contempla análisis en vivo ni procesamiento *in-play*.
3. **Cobertida Deportiva y Geográfica:** Restringido a partidos de fútbol de las ligas europeas seleccionadas en la Etapa 1.
4. **Lógica de Modelado:** Se excluye la predicción directa de resultados finales (Mercado 1X2). [cite_start]El enfoque es 100% probabilístico sobre eventos de volumen (córneres, faltas, saques de banda).
5. **Scraping de Arbitraje:** No incluye scraping multifuente en paralelo para la búsqueda de *Surebets*.
6. **Interfaz y Frontend:** No incluye el desarrollo de un Dashboard Web ni aplicación móvil; la interacción se realizará a nivel de consola y scripts ejecutables.

## 1.3 Objetivos del Proyecto:

### Objetivo general:

Desarrollar un sistema automatizado de extracción de datos (Pipeline ETL) y un modelo predictivo de Machine Learning capaz de analizar 
estadísticas históricas de fútbol, con el fin de proyectar escenarios de partido e identificar cuotas de valor (Value Bets) en los mercados deportivos.

### Objetivos Específicos:

El software tiene como objetivo predicir las estadísticas de los partidos:

  1. Objetivo de Ingeniería de Datos: Construir un motor de web scraping y una base de datos relacional capaz de extraer, 
limpiar y almacenar el 100% de las estadísticas clave de los partidos de las ligas seleccionadas de forma automatizada.
  2. Objetivo de Predicción Conservadora (Bajo Riesgo): Entrenar un modelo de clasificación que logre predecir estadísticas 
de volumen (ej. Over de córneres, saques de banda o faltas) con una tasa de acierto (Accuracy) igual o superior al 70%, sirviendo 
como escudo financiero para la estrategia.
  3. Objetivo de Predicción de Alto Riesgo: Desarrollar un algoritmo que logre identificar ineficiencias en cuotas de alto valor 
(Hándicaps, resultados exactos), logrando un retorno de inversión (ROI) positivo a largo plazo, superando la probabilidad matemática 
implícita de las casas de apuestas.

---

# 2. Especificación de Requisitos

## 2.1. Requisitos Funcionales
| ID | Nombre | Descripción |
| :--- | :--- | :--- |
| **RF-01** | Crawling de URLs | Extracción de enlaces de partidos por liga y temporada. |
| **RF-02** | Interceptación API | Captura de respuestas JSON directamente de la red mediante Playwright. |
| **RF-03** | Pipeline ETL | Limpieza, estructuración y filtrado de estadísticas cuantitativas de volumen. |
| **RF-04** | Carga a BD | Inyección de datos transformados a SQLite (`oraculo.db`). |
| **RF-05** | Modelo Predictivo | Estimación de probabilidades para eventos de volumen (córneres, faltas, etc.). |

## 2.2. Requisitos No Funcionales
| ID | Nombre | Descripción |
| :--- | :--- | :--- |
| **RNF-01** | Comportamiento Humano | Incorporación de pausas aleatorias para mitigar detección anti-scraping. |
| **RNF-02** | Parametrización | Configuración centralizada vía `json/yaml` independiente del código. |
| **RNF-03** | Portabilidad | Manejo de rutas relativas con `os.path` respecto a la raíz del proyecto. |
| **RNF-04** | Integridad Referencial | Control estricto de claves foráneas en la base de datos relacional. |

---

# 3. Arquitectura del Sistema y Diseño

## 3.1 Arquitectura de Carpetas y Módulos.

El proyecto "Oráculo" sigue un diseño modular. Esto permite separar las responsabilidades (extracción, transformación, 
base de datos y configuración) para que el código sea mantenible, escalable y a prueba de errores. 

La estructura de directorios del proyecto se organiza de la siguiente manera:

```text
oraculo_project/
│
├── main.py                  # "Director de Orquesta": Punto de entrada único que orquesta los scripts.
├── config.json              # Archivo de configuración (rutas, parámetros de ligas, temporadas).
│
├── scrapers/                # Módulo de Extracción (Web Scraping)
│   ├── match_crawler.py     # Navega por el DOM y extrae las URLs/IDs de los partidos de la liga por rondas.
│   └── stats_scraper.py     # Intercepta el tráfico de red con Playwright y descarga los JSON de estadísticas.
│
├── etl/                     # Módulo de Transformación (Procesamiento de Datos)
│   ├── json_processor.py    # Itera sobre la carpeta de descargas para aplanar los JSON.
│   └── data_cleaner.py      # Utiliza Pandas para limpiar, castear tipos y estructurar los DataFrames.
│
├── database/                # Módulo de Carga y Modelado (Base de Datos)
│   ├── crear_db.py          # Script DDL (Data Definition Language) para inicializar tablas y FKs (SQLite).
│   └── db_manager.py        # Gestiona la conexión e inyecta los datos limpios (ej. mediante .to_sql()).
│
├── utils/                   # Herramientas Transversales compartidas por todos los módulos
│   ├── base.py              # Funciones auxiliares genéricas (ej. random_sleep() para scraping ético).
│   ├── logger.py            # Configuración de los logs de ejecución del sistema.
│   └── json_reader.py       # Utilidades para cargar parámetros del config.json.
│
├── ml_models                # Carpeta par almacenar los modelos de machine learning para consuman la database
│
└── data/                    # Almacenamiento local temporal (Ignorado en repositorios git)
    ├── matchs_stats/           # Archivos JSON crudos de estadisticas de los partidos.
    └── urls_league_rounds/     # Archivos JSON generados para almacenar las urls de los partidos por rondas.
```


## 3.2 Pipeline de Datos.

El flujo de vida de los datos sigue un proceso clásico de Ingeniería de Datos ETL (Extracción, Transformación y Carga), 
diseñado para ejecutarse de manera secuencial y automatizada:

### Fase 1: Extracción (Extract)
* Herramientas: Python + Playwright.

* Proceso: El orquestador (main.py) invoca a los scrapers. Utilizando Playwright, el bot navega como un humano (aplicando 
pausas tácticas con random_sleep), hace clic en las pestañas de estadísticas y escucha el tráfico de red (Network Interception) 
para atrapar directamente las respuestas JSON de la API oculta del servidor (ej. Sofascore).

* Salida: Archivos unitarios .json por cada partido guardados en data/raw_jsons/.

### Fase 2: Transformación (Transform)
* Herramientas: Python + Pandas.

* Proceso: El módulo ETL lee los JSON crudos almacenados. Aísla los bloques clave (filtrando por partido completo 'ALL' o 
tiempos '1ST'/'2ST'). A continuación, a través de DataFrames de Pandas, se limpian los datos: se eliminan símbolos basura 
(como % o km), se castean variables a números flotantes o enteros, y se renuevan las claves para que coincidan con los atributos de la base de datos.

* Salida: Estructuras de datos (DataFrames) limpias, normalizadas y listas para relacionarse.

### Fase 3: Carga (Load)
* Herramientas: Python + SQLite (vía SQLAlchemy o conector nativo).

* Proceso: Se inicializa la base de datos ejecutando crear_db.py (asegurando PRAGMA foreign_keys = ON). Posteriormente, se 
inyectan los DataFrames limpios a las tablas correspondientes respetando la jerarquía relacional estricta: 
PAIS -> LIGAS -> EQUIPOS -> PARTIDOS -> ESTADISTICAS_PARTIDO.

* Salida: Base de datos relacional robusta, con historiales de partidos listos para ser consultados mediante SQL.

### Fase 4: Consumo (Machine Learning - Trabajo Futuro)
* Proceso: Una vez el pipeline ETL estabilicé la base de datos, los modelos predictivos (Clasificación/Regresión) leerán 
directamente de las tablas para encontrar Value Bets e ineficiencias de cuotas en las estadísticas de volumen (córneres, saques de banda, faltas).

## 3.3 Modelo de Datos 

### Diccionario de Datos

#### Entidad: PAIS
> **Descripción:** Entidad maestra que almacena el catálogo de países registrados.

| Atributo | Tipo de datos | Tipo de clave | Límite de caracteres | Nulo |
| :--- | :--- | :--- | :--- | :--- |
| **Id_pais** | `TINYINT` | **PK** | 10 | No |
| **Nombre_pais** | `VARCHAR` | Ninguna | 20 | No |

---

#### Entidad: LIGAS
> **Descripción:** Catálogo de competiciones o ligas asociadas a un país.

| Atributo | Tipo de datos | Tipo de clave | Límite de caracteres | Nulo |
| :--- | :--- | :--- | :--- | :--- |
| **Id_liga** | `SMALLINT` | **PK** | 10 | No |
| **Nombre_liga** | `VARCHAR` | Ninguna | 20 | No |
| **Rondas** | `TINYINT` | Ninguna | 2 | No |
| **Temporada** | `VARCHAR` | Ninguna | 5 | No |
| **Id_pais** | `TINYINT` | **FK** | 10 | No |

---

#### Entidad: EQUIPOS
> **Descripción:** Entidad que representa a los clubes y selecciones.

| Atributo | Tipo de datos | Tipo de clave | Límite de caracteres | Nulo |
| :--- | :--- | :--- | :--- | :--- |
| **Id_equipo** | `SMALLINT` | **PK** | 10 | No |
| **Nombre_equipo** | `VARCHAR` | Ninguna | 20 | No |
| **Id_liga** | `SMALLINT` | **FK** | 10 | No |
| **Id_pais** | `TINYINT` | **FK** | 10 | No |

---

#### Entidad: JUGADORES
> **Descripción:** Entidad que representa a los jugadores.

| Atributo               | Tipo de datos | Tipo de clave | Límite de caracteres | Nulo |
|:-----------------------|:--------------|:--------------|:---------------------| :--- |
| **Id_jugador**         | `SMALLINT`    | **PK**        | 10                   | No |
| **Nombre_jugador**     | `VARCHAR`     | Ninguna       | 50                   | No |
| **Id_equipo**          | `SMALLINT`    | **FK**        | 10                   | No |
| **Id_pais**            | `TINYINT`     | **FK**        | 10                   | No |
| **Estatura**           | `TINYINT`     | **Ninguna**   | 10                   | No |
| **Fecha_Nacimiento**   | `DATE`        | **Ninguna**   | 10                   | No |
| **Genero**             | `VARCHAR`     | **Ninguna**   | 10                   | No |
| **Posicion_principal** | `VARCHAR`     | **Ninguna**   | 10                   | No |

---

#### Entidad: ALINEACION
> **Descripción:** Entidad que representa la alineacion y posicion de los jugadores en el partidos.

| Atributo             | Tipo de datos | Tipo de clave | Límite de caracteres | Nulo |
|:---------------------|:--------------|:--------------|:---------------------| :--- |
| **Id_jugador**       | `SMALLINT`    | **PK**        | 10                   | No |
| **Id_partido**       | `SMALLINT`    | **PK**        | 50                   | No |
| **Id_equipo**        | `SMALLINT`    | **FK**        | 10                   | No |
| **Titular**          | `TINYINT`     | **FK**        | 10                   | No |
| **Suplente**         | `TINYINT`     | **Ninguna**   | 10                   | No |
| **Posicion_partido** | `DATE`        | **Ninguna**   | 10                   | No |
| **Dorsal**           | `VARCHAR`     | **Ninguna**   | 10                   | No |
| **Formacion**        | `VARCHAR`     | **Ninguna**   | 10                   | No |

---

#### Entidad: PARTIDOS
> **Descripción:** Entidad transaccional que registra los enfrentamientos deportivos.

| Atributo | Tipo de datos | Tipo de clave | Límite de caracteres | Nulo |
| :--- | :--- | :--- | :--- | :--- |
| **Id_partido** | `INT` | **PK** | 10 | No |
| **Id_liga** | `SMALLINT` | **FK** | 10 | No |
| **Id_equipo_visita**| `SMALLINT` | **FK** | 10 | No |
| **Id_equipo_local** | `SMALLINT` | **FK** | 10 | No |
| **Fecha** | `DATE` | Ninguna | N/A | No |
| **Goles_visita** | `SMALLINT` | Ninguna | N/A | No |
| **Goles_local** | `SMALLINT` | Ninguna | N/A | No |
| **Url** | `TEXT` | Ninguna | N/A | No |

---

#### Entidad: JUGADORES_ESTADISTICAS
> **Descripción:** Entidad analitica que almacena el rendimiento de los jugadores

| Atributo                                       | Tipo de datos | Tipo de clave | Límite de caracteres | Nulo |
|:-----------------------------------------------|:--------------| :--- | :--- | :--- |
| **Id_jugador**                                 | `INT`         | **PK / FK** | 10 | No |
| **Id_partido**                                 | `INT`         | **PK / FK** | 10 | No |
| **Id_equipo**                                  | `SMALLINT`    | **PK / FK** | 10 | No |
| **Minutos_jugados**                            | `TINYINT`     | Ninguna | N/A | No |
| **Condicion_local**                            | `BOOLEAN`     | Ninguna | N/A | No |
| **Posesion_balon**                             | `DECIMAL`     | Ninguna | N/A | Sí |
| **Distancia_recorrida_km**                     | `DECIMAL`     | Ninguna | N/A | Sí |
| **Goles_esperados_xG**                         | `DECIMAL`     | Ninguna | N/A | Sí |
| **Grandes_ocasiones**                          | `TINYINT`     | Ninguna | N/A | Sí |
| **Sprints**                                    | `SMALLINT`    | Ninguna | N/A | Sí |
| **Corners**                                    | `TINYINT`     | Ninguna | N/A | Sí |
| **Faltas**                                     | `TINYINT`     | Ninguna | N/A | Sí |
| **Pases**                                      | `SMALLINT`    | Ninguna | N/A | Sí |
| **Entradas**                                   | `TINYINT`     | Ninguna | N/A | Sí |
| **Tiros_libres**                               | `TINYINT`     | Ninguna | N/A | Sí |
| **Tarjetas_amarillas**                         | `TINYINT`     | Ninguna | N/A | Sí |
| **Tarjetas_rojas**                             | `TINYINT`     | Ninguna | N/A | Sí |
| **Remates**                                    | `TINYINT`     | Ninguna | N/A | Sí |
| **Tiros_arco**                                 | `TINYINT`     | Ninguna | N/A | Sí |
| **Tiros_al_palo**                              | `TINYINT`     | Ninguna | N/A | Sí |
| **Tiros_fuera**                                | `TINYINT`     | Ninguna | N/A | Sí |
| **Tiros_bloqueados**                           | `TINYINT`     | Ninguna | N/A | Sí |
| **Tiros_adentro_del_area**                     | `TINYINT`     | Ninguna | N/A | Sí |
| **Tiros_afuera_del_area**                      | `TINYINT`     | Ninguna | N/A | Sí |
| **Ocasiones_claras_realizadas**                | `TINYINT`     | Ninguna | N/A | Sí |
| **Ocasiones_claras_falladas**                  | `TINYINT`     | Ninguna | N/A | Sí |
| **Toques_dentro_del_area**                     | `TINYINT`     | Ninguna | N/A | Sí |
| **Faltas_recibidas_ultima_tercio**             | `TINYINT`     | Ninguna | N/A | Sí |
| **Fueras_de_juego**                            | `TINYINT`     | Ninguna | N/A | Sí |
| **Pases_precisos**                             | `SMALLINT`    | Ninguna | N/A | Sí |
| **Saques_de_banda**                            | `TINYINT`     | Ninguna | N/A | Sí |
| **Pases_al_ultimo_tercio**                     | `SMALLINT`    | Ninguna | N/A | Sí |
| **Total_pases_area_penal_adversaria**          | `SMALLINT`    | Ninguna | N/A | Sí |
| **Total_pases_precisos_area_penal_adversaria** | `SMALLINT`    | Ninguna | N/A | Sí |
| **Total_balones_largos**                       | `SMALLINT`    | Ninguna | N/A | Sí |
| **Total_balones_largos_precisos**              | `SMALLINT`    | Ninguna | N/A | Sí |
| **Total_centros**                              | `TINYINT`     | Ninguna | N/A | Sí |
| **Total_centros_exitosos**                     | `TINYINT`     | Ninguna | N/A | Sí |
| **Porcentaje_duelos_ganados**                  | `DECIMAL`     | Ninguna | N/A | Sí |
| **Balones_perdidos**                           | `TINYINT`     | Ninguna | N/A | Sí |
| **Total_duelos_suelo**                         | `SMALLINT`    | Ninguna | N/A | Sí |
| **Total_duelos_suelo_ganados**                 | `SMALLINT`    | Ninguna | N/A | Sí |
| **Total_duelos_aereos**                        | `SMALLINT`    | Ninguna | N/A | Sí |
| **Total_duelos_aereos_ganados**                | `SMALLINT`    | Ninguna | N/A | Sí |
| **Total_regates**                              | `TINYINT`     | Ninguna | N/A | Sí |
| **Total_regates_ganados**                      | `TINYINT`     | Ninguna | N/A | Sí |
| **Total_entradas**                             | `TINYINT`     | Ninguna | N/A | Sí |
| **Total_entradas_ganadas**                     | `TINYINT`     | Ninguna | N/A | Sí |
| **Porcentaje_entradas_ganadas**                | `DECIMAL`     | Ninguna | N/A | Sí |
| **Intercepciones**                             | `TINYINT`     | Ninguna | N/A | Sí |
| **Recuperaciones**                             | `TINYINT`     | Ninguna | N/A | Sí |
| **Despejes**                                   | `TINYINT`     | Ninguna | N/A | Sí |
| **Errores_terminan_tiro**                      | `TINYINT`     | Ninguna | N/A | Sí |
| **Errores_terminan_gol**                       | `TINYINT`     | Ninguna | N/A | Sí |
| **Atajadas**                                   | `TINYINT`     | Ninguna | N/A | Sí |
| **Goles_evitados**                             | `DECIMAL`     | Ninguna | N/A | Sí |
| **Grandes_atajadas**                           | `TINYINT`     | Ninguna | N/A | Sí |
| **Balones_aereos_atrapados**                   | `TINYINT`     | Ninguna | N/A | Sí |
| **Despejes_punos**                             | `TINYINT`     | Ninguna | N/A | Sí |
| **Saques_de_arco**                             | `TINYINT`     | Ninguna | N/A | Sí |

---

#### Entidad: PARTIDOS_ESTADISTICAS
> **Descripción:** Entidad analítica granular de rendimiento por equipo y período.

| Atributo                                       | Tipo de datos | Tipo de clave | Límite de caracteres | Nulo |
|:-----------------------------------------------|:--------------| :--- | :--- | :--- |
| **Id_partido**                                 | `INT`         | **PK / FK** | 10 | No |
| **Id_equipo**                                  | `SMALLINT`    | **PK / FK** | 10 | No |
| **Periodo**                                    | `VARCHAR`     | **PK** | 10 | No |
| **Condicion_local**                            | `BOOLEAN`     | Ninguna | N/A | No |
| **Posesion_balon**                             | `DECIMAL`     | Ninguna | N/A | Sí |
| **Distancia_recorrida_km**                     | `DECIMAL`     | Ninguna | N/A | Sí |
| **Goles_esperados_xG**                         | `DECIMAL`     | Ninguna | N/A | Sí |
| **Grandes_ocasiones**                          | `TINYINT`     | Ninguna | N/A | Sí |
| **Sprints**                                    | `SMALLINT`    | Ninguna | N/A | Sí |
| **Corners**                                    | `TINYINT`     | Ninguna | N/A | Sí |
| **Faltas**                                     | `TINYINT`     | Ninguna | N/A | Sí |
| **Pases**                                      | `SMALLINT`    | Ninguna | N/A | Sí |
| **Entradas**                                   | `TINYINT`     | Ninguna | N/A | Sí |
| **Tiros_libres**                               | `TINYINT`     | Ninguna | N/A | Sí |
| **Tarjetas_amarillas**                         | `TINYINT`     | Ninguna | N/A | Sí |
| **Tarjetas_rojas**                             | `TINYINT`     | Ninguna | N/A | Sí |
| **Remates**                                    | `TINYINT`     | Ninguna | N/A | Sí |
| **Tiros_arco**                                 | `TINYINT`     | Ninguna | N/A | Sí |
| **Tiros_al_palo**                              | `TINYINT`     | Ninguna | N/A | Sí |
| **Tiros_fuera**                                | `TINYINT`     | Ninguna | N/A | Sí |
| **Tiros_bloqueados**                           | `TINYINT`     | Ninguna | N/A | Sí |
| **Tiros_adentro_del_area**                     | `TINYINT`     | Ninguna | N/A | Sí |
| **Tiros_afuera_del_area**                      | `TINYINT`     | Ninguna | N/A | Sí |
| **Ocasiones_claras_realizadas**                | `TINYINT`     | Ninguna | N/A | Sí |
| **Ocasiones_claras_falladas**                  | `TINYINT`     | Ninguna | N/A | Sí |
| **Toques_dentro_del_area**                     | `TINYINT`     | Ninguna | N/A | Sí |
| **Faltas_recibidas_ultima_tercio**             | `TINYINT`     | Ninguna | N/A | Sí |
| **Fueras_de_juego**                            | `TINYINT`     | Ninguna | N/A | Sí |
| **Pases_precisos**                             | `SMALLINT`    | Ninguna | N/A | Sí |
| **Saques_de_banda**                            | `TINYINT`     | Ninguna | N/A | Sí |
| **Pases_al_ultimo_tercio**                     | `SMALLINT`    | Ninguna | N/A | Sí |
| **Total_pases_area_penal_adversaria**          | `SMALLINT`    | Ninguna | N/A | Sí |
| **Total_pases_precisos_area_penal_adversaria** | `SMALLINT`    | Ninguna | N/A | Sí |
| **Total_balones_largos**                       | `SMALLINT`    | Ninguna | N/A | Sí |
| **Total_balones_largos_precisos**              | `SMALLINT`    | Ninguna | N/A | Sí |
| **Total_centros**                              | `TINYINT`     | Ninguna | N/A | Sí |
| **Total_centros_exitosos**                     | `TINYINT`     | Ninguna | N/A | Sí |
| **Porcentaje_duelos_ganados**                  | `DECIMAL`     | Ninguna | N/A | Sí |
| **Balones_perdidos**                           | `TINYINT`     | Ninguna | N/A | Sí |
| **Total_duelos_suelo**                         | `SMALLINT`    | Ninguna | N/A | Sí |
| **Total_duelos_suelo_ganados**                 | `SMALLINT`    | Ninguna | N/A | Sí |
| **Total_duelos_aereos**                        | `SMALLINT`    | Ninguna | N/A | Sí |
| **Total_duelos_aereos_ganados**                | `SMALLINT`    | Ninguna | N/A | Sí |
| **Total_regates**                              | `TINYINT`     | Ninguna | N/A | Sí |
| **Total_regates_ganados**                      | `TINYINT`     | Ninguna | N/A | Sí |
| **Total_entradas**                             | `TINYINT`     | Ninguna | N/A | Sí |
| **Total_entradas_ganadas**                     | `TINYINT`     | Ninguna | N/A | Sí |
| **Porcentaje_entradas_ganadas**                | `DECIMAL`     | Ninguna | N/A | Sí |
| **Intercepciones**                             | `TINYINT`     | Ninguna | N/A | Sí |
| **Recuperaciones**                             | `TINYINT`     | Ninguna | N/A | Sí |
| **Despejes**                                   | `TINYINT`     | Ninguna | N/A | Sí |
| **Errores_terminan_tiro**                      | `TINYINT`     | Ninguna | N/A | Sí |
| **Errores_terminan_gol**                       | `TINYINT`     | Ninguna | N/A | Sí |
| **Atajadas**                                   | `TINYINT`     | Ninguna | N/A | Sí |
| **Goles_evitados**                             | `DECIMAL`     | Ninguna | N/A | Sí |
| **Grandes_atajadas**                           | `TINYINT`     | Ninguna | N/A | Sí |
| **Balones_aereos_atrapados**                   | `TINYINT`     | Ninguna | N/A | Sí |
| **Despejes_punos**                             | `TINYINT`     | Ninguna | N/A | Sí |
| **Saques_de_arco**                             | `TINYINT`     | Ninguna | N/A | Sí |

---

### 3.2. Modelo Relacional No Gráfico

#### a. Entidades Maestras
Son tablas independientes que sirven como catálogos base para el sistema.

* **`PAIS`**: Es la entidad raíz geográfica. Se vincula con `LIGAS` y `EQUIPOS` mediante su clave primaria (`Id_pais`). 
  * **Cardinalidad:** `1:N` (un país puede albergar múltiples ligas y equipos).

#### b. Entidades Intermedias / Catálogos Operativos
Dependen de las entidades maestras y estructuran el marco competitivo.

* **`LIGAS`**: Hereda la clave foránea `Id_pais`. Se vincula con `EQUIPOS` y `PARTIDOS` mediante su clave primaria (`Id_liga`). 
  * **Cardinalidad:** `1:N` (una liga agrupa a múltiples equipos).
* **`EQUIPOS`**: Hereda las claves foráneas `Id_liga` e `Id_pais`. Se vincula con `PARTIDOS` (como local y visitante) y con `PARTIDOS_ESTADISTICAS` mediante su clave primaria (`Id_equipo`). 
  * **Cardinalidad:** `1:N` por cada rol (local/visitante).

#### c. Entidades de Flujo Transaccional y Control Operativo
Registran los eventos reales y el volumen de datos analíticos.

* **`PARTIDOS`**: Representa cada encuentro deportivo. Hereda la clave foránea `Id_liga` y se conecta a `EQUIPOS` mediante dos claves foráneas 
(`Id_equipo_local` e `Id_equipo_visita`). Se relaciona con `PARTIDOS_ESTADISTICAS` a través de su clave primaria (`Id_partido`).
  * **Cardinalidad:** `1:N` (un partido genera múltiples registros de estadísticas).
* **`PARTIDOS_ESTADISTICAS`**:Entidad analítica granular. Hereda las claves foráneas `Id_partido` e `Id_equipo`. 
Posee una clave primaria compuesta formada por `(Id_partido, Id_equipo, Periodo)`, lo que garantiza la unicidad e integridad de los datos de rendimiento para un equipo y período específico en cada partido.

# 4. Roadmap y Planificación por Etapas

El desarrollo del Proyecto "Oráculo" se ejecutará bajo un enfoque iterativo e incremental, dividido en cuatro grandes fases. 
Esto garantiza la entrega de valor temprano (MVP) antes de escalar hacia modelos predictivos complejos.

# 5. Estrategia de Pruebas y Calidad

# 6. Gestión de Riesgos y Mitigación

# 7. Estándares y Convenciones de Código