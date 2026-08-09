# Diccionario de Datos y Modelo Lógico de Base de Datos

---

## 1. Diccionario de Datos

### Entidad: PAIS
> **Descripción:** Entidad maestra que almacena el catálogo de países registrados.

| Atributo | Tipo de datos | Tipo de clave | Límite de caracteres | Nulo |
| :--- | :--- | :--- | :--- | :--- |
| **Id_pais** | `TINYINT` | **PK** | 10 | No |
| **Nombre_pais** | `VARCHAR` | Ninguna | 20 | No |

---

### Entidad: LIGAS
> **Descripción:** Catálogo de competiciones o ligas asociadas a un país.

| Atributo | Tipo de datos | Tipo de clave | Límite de caracteres | Nulo |
| :--- | :--- | :--- | :--- | :--- |
| **Id_liga** | `SMALLINT` | **PK** | 10 | No |
| **Nombre_liga** | `VARCHAR` | Ninguna | 20 | No |
| **Rondas** | `TINYINT` | Ninguna | 2 | No |
| **Temporada** | `VARCHAR` | Ninguna | 5 | No |
| **Id_pais** | `TINYINT` | **FK** | 10 | No |

---

### Entidad: EQUIPOS
> **Descripción:** Entidad que representa a los clubes y selecciones.

| Atributo | Tipo de datos | Tipo de clave | Límite de caracteres | Nulo |
| :--- | :--- | :--- | :--- | :--- |
| **Id_equipo** | `SMALLINT` | **PK** | 10 | No |
| **Nombre_equipo** | `VARCHAR` | Ninguna | 20 | No |
| **Id_liga** | `SMALLINT` | **FK** | 10 | No |
| **Id_pais** | `TINYINT` | **FK** | 10 | No |

---

### Entidad: PARTIDOS
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

### Entidad: PARTIDOS_ESTADISTICAS
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

## 2. Modelo Relacional No Gráfico

### 1. Entidades Maestras
Son tablas independientes que sirven como catálogos base para el sistema.

* **`PAIS`**: Es la entidad raíz geográfica. Se vincula con `LIGAS` y `EQUIPOS` mediante su clave primaria (`Id_pais`). 
  * **Cardinalidad:** `1:N` (un país puede albergar múltiples ligas y equipos).

### 2. Entidades Intermedias / Catálogos Operativos
Dependen de las entidades maestras y estructuran el marco competitivo.

* **`LIGAS`**: Hereda la clave foránea `Id_pais`. Se vincula con `EQUIPOS` y `PARTIDOS` mediante su clave primaria (`Id_liga`). 
  * **Cardinalidad:** `1:N` (una liga agrupa a múltiples equipos).
* **`EQUIPOS`**: Hereda las claves foráneas `Id_liga` e `Id_pais`. Se vincula con `PARTIDOS` (como local y visitante) y con `PARTIDOS_ESTADISTICAS` mediante su clave primaria (`Id_equipo`). 
  * **Cardinalidad:** `1:N` por cada rol (local/visitante).

### 3. Entidades de Flujo Transaccional y Control Operativo
Registran los eventos reales y el volumen de datos analíticos.

* **`PARTIDOS`**: Representa cada encuentro deportivo. Hereda la clave foránea `Id_liga` y se conecta a `EQUIPOS` mediante dos claves foráneas (`Id_equipo_local` e `Id_equipo_visita`). Se relaciona con `PARTIDOS_ESTADISTICAS` a través de su clave primaria (`Id_partido`).
  * **Cardinalidad:** `1:N` (un partido genera múltiples registros de estadísticas).
* **`PARTIDOS_ESTADISTICAS`**: Entidad analítica granular. Hereda las claves foráneas `Id_partido` e `Id_equipo`. Posee una clave primaria compuesta formada por `(Id_partido, Id_equipo, Periodo)`, lo que garantiza la unicidad e integridad de los datos de rendimiento para un equipo y período específico en cada partido.