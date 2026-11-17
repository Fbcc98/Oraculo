# Modelo de datos

## Índice

- [Diccionario SQLite vigente](#diccionario-sqlite)
- [Del diseño al código](#del-diseño-al-código)
- [Diseño original](#diseño-original)
  - [Catálogos y partidos](#catálogos-y-partidos)
  - [Estadísticas de jugadores](#estadísticas-de-jugadores)
  - [Estadísticas de partidos](#estadísticas-de-partidos)
  - [Relaciones originales](#relaciones-originales)

PAIS es la entidad maestra. LIGAS, EQUIPOS, JUGADORES y ALINEACION son entidades intermedias. PARTIDOS, PARTIDOS_ESTADISTICAS y JUGADORES_ESTADISTICAS registran encuentros y métricas. ENTRENADORES, PARTIDOS_EQUIPOS y ENTRENADORES_PARTIDO completan el esquema.

Un país agrupa ligas y una liga agrupa partidos. PARTIDOS_EQUIPOS identifica cada participante y limita a uno por condición local o visitante. ALINEACION vincula al jugador con su equipo en el encuentro. Las estadísticas se almacenan por equipo y período o por jugador y partido.

## Diccionario SQLite

Cada fila agrupa atributos del mismo tipo en la misma tabla. Las claves compuestas se muestran en orden. [Definición SQL](../database/crear_db.py)

### PAIS

| Tipo | Atributos |
|---|---|
| INTEGER | `Id_pais` |
| TEXT | `Codigo_alpha3`, `Nombre_pais` |

PK: `(Id_pais)`.

Sin FK.

### LIGAS

| Tipo | Atributos |
|---|---|
| INTEGER | `Id_liga`, `Id_pais`, `Id_temporada_externo` |
| TEXT | `Nombre_liga`, `Temporada` |

PK: `(Id_liga)`.

FK: `(Id_pais)` → `PAIS(Id_pais)`.

### EQUIPOS

| Tipo | Atributos |
|---|---|
| INTEGER | `Id_equipo`, `Id_pais` |
| TEXT | `Nombre_equipo`, `Slug` |

PK: `(Id_equipo)`.

FK: `(Id_pais)` → `PAIS(Id_pais)`.

### JUGADORES

| Tipo | Atributos |
|---|---|
| INTEGER | `Id_jugador`, `Id_pais`, `Estatura_cm` |
| TEXT | `Nombre_jugador`, `Nombre_corto`, `Slug`, `Fecha_nacimiento`, `Genero`, `Posicion_principal` |

PK: `(Id_jugador)`.

FK: `(Id_pais)` → `PAIS(Id_pais)`.

### ENTRENADORES

| Tipo | Atributos |
|---|---|
| INTEGER | `Id_entrenador` |
| TEXT | `Nombre_entrenador`, `Nombre_corto`, `Slug` |

PK: `(Id_entrenador)`.

Sin FK.

### PARTIDOS

| Tipo | Atributos |
|---|---|
| INTEGER | `Id_partido`, `Id_liga`, `Ronda`, `Goles_local`, `Goles_visita`, `Alineacion_confirmada` |
| TEXT | `Fecha_hora_utc`, `Url` |

PK: `(Id_partido)`.

FK: `(Id_liga)` → `LIGAS(Id_liga)`.

### PARTIDOS_EQUIPOS

| Tipo | Atributos |
|---|---|
| INTEGER | `Id_partido`, `Id_equipo`, `Condicion_local` |
| TEXT | `Formacion`, `Color_jugadores`, `Color_portero` |

PK: `(Id_partido, Id_equipo)`.

FK: `(Id_equipo)` → `EQUIPOS(Id_equipo)`.

FK: `(Id_partido)` → `PARTIDOS(Id_partido)`.

### ENTRENADORES_PARTIDO

| Tipo | Atributos |
|---|---|
| INTEGER | `Id_partido`, `Id_equipo`, `Id_entrenador` |

PK: `(Id_partido, Id_equipo)`.

FK: `(Id_entrenador)` → `ENTRENADORES(Id_entrenador)`.

FK: `(Id_partido, Id_equipo)` → `PARTIDOS_EQUIPOS(Id_partido, Id_equipo)`.

### ALINEACION

| Tipo | Atributos |
|---|---|
| INTEGER | `Id_partido`, `Id_jugador`, `Id_equipo`, `Es_titular`, `Dorsal` |
| TEXT | `Posicion_partido` |

PK: `(Id_partido, Id_jugador)`.

FK: `(Id_jugador)` → `JUGADORES(Id_jugador)`.

FK: `(Id_partido, Id_equipo)` → `PARTIDOS_EQUIPOS(Id_partido, Id_equipo)`.

### PARTIDOS_ESTADISTICAS

| Tipo | Atributos |
|---|---|
| INTEGER | `Id_partido`, `Id_equipo`, `Grandes_ocasiones`, `Sprints`, `Corners`, `Faltas`, `Pases`, `Entradas` |
| INTEGER | `Tiros_libres`, `Tarjetas_amarillas`, `Tarjetas_rojas`, `Remates`, `Tiros_arco`, `Tiros_al_palo`, `Tiros_fuera`, `Tiros_bloqueados` |
| INTEGER | `Tiros_adentro_del_area`, `Tiros_afuera_del_area`, `Ocasiones_claras_realizadas`, `Ocasiones_claras_falladas`, `Toques_dentro_del_area`, `Faltas_recibidas_ultimo_tercio`, `Fueras_de_juego`, `Pases_precisos` |
| INTEGER | `Saques_de_banda`, `Entradas_ultimo_tercio`, `Total_pases_area_penal_adversaria`, `Pases_precisos_area_penal_adversaria`, `Total_balones_largos`, `Balones_largos_precisos`, `Total_centros`, `Centros_exitosos` |
| INTEGER | `Balones_perdidos`, `Total_duelos_suelo`, `Duelos_suelo_ganados`, `Total_duelos_aereos`, `Duelos_aereos_ganados`, `Total_regates`, `Regates_ganados`, `Total_entradas` |
| INTEGER | `Entradas_ganadas`, `Intercepciones`, `Recuperaciones`, `Despejes`, `Errores_terminan_tiro`, `Errores_terminan_gol`, `Atajadas`, `Grandes_atajadas` |
| INTEGER | `Balones_aereos_atrapados`, `Despejes_punos`, `Saques_de_arco` |
| TEXT | `Periodo` |
| REAL | `Posesion_balon`, `Distancia_recorrida_km`, `Goles_esperados_xG`, `Porcentaje_duelos_ganados`, `Goles_evitados` |

PK: `(Id_partido, Id_equipo, Periodo)`.

FK: `(Id_partido, Id_equipo)` → `PARTIDOS_EQUIPOS(Id_partido, Id_equipo)`.

### JUGADORES_ESTADISTICAS

| Tipo | Atributos |
|---|---|
| INTEGER | `Id_partido`, `Id_jugador`, `Id_equipo`, `Minutos_jugados`, `Goles`, `Asistencias`, `Remates`, `Remates_arco` |
| INTEGER | `Remates_fuera`, `Remates_bloqueados`, `Tiros_al_palo`, `Grandes_ocasiones_creadas`, `Grandes_ocasiones_falladas`, `Pases`, `Pases_precisos`, `Pases_clave` |
| INTEGER | `Pases_campo_propio`, `Pases_precisos_campo_propio`, `Pases_campo_rival`, `Pases_precisos_campo_rival`, `Balones_largos`, `Balones_largos_precisos`, `Centros`, `Centros_precisos` |
| INTEGER | `Regates`, `Regates_ganados`, `Duelos_ganados`, `Duelos_perdidos`, `Duelos_aereos_ganados`, `Duelos_aereos_perdidos`, `Entradas`, `Entradas_ganadas` |
| INTEGER | `Intercepciones`, `Recuperaciones`, `Despejes`, `Bloqueos`, `Faltas_cometidas`, `Faltas_recibidas`, `Fueras_de_juego`, `Perdidas_posesion` |
| INTEGER | `Desposesiones`, `Controles_fallidos`, `Toques`, `Conducciones_balon`, `Conducciones_progresivas`, `Sprints`, `Desafios_perdidos`, `Despejes_linea_gol` |
| INTEGER | `Entradas_ultimo_hombre`, `Errores_terminan_remate`, `Errores_terminan_gol`, `Autogoles`, `Penales_cometidos`, `Penales_recibidos`, `Atajadas`, `Atajadas_dentro_area` |
| INTEGER | `Salidas_portero`, `Salidas_portero_precisas`, `Centros_altos_atrapados`, `Despejes_punos`, `Penales_enfrentados` |
| REAL | `Rating`, `Goles_esperados_xG`, `Asistencias_esperadas_xA`, `Goles_esperados_al_arco_xGOT`, `Distancia_conduccion_balon`, `Distancia_conduccion_progresiva`, `Progresion_total`, `Mejor_progresion_conduccion` |
| REAL | `Distancia_recorrida_km`, `Velocidad_maxima`, `Distancia_corriendo_km`, `Distancia_alta_velocidad_km`, `Distancia_sprint_km`, `Valor_atajadas_portero`, `Goles_evitados`, `Rating_original` |
| REAL | `Rating_alternativo` |

PK: `(Id_partido, Id_jugador)`.

FK: `(Id_partido, Id_equipo)` → `PARTIDOS_EQUIPOS(Id_partido, Id_equipo)`.

FK: `(Id_partido, Id_jugador)` → `ALINEACION(Id_partido, Id_jugador)`.

## Del diseño al código

El [esquema SQLite](../database/crear_db.py) define las tablas que crea la aplicación. El [plan de la carga piloto](otros/PROXIMA_SESION.md) recoge los acuerdos sobre identificadores, fechas y partidos finalizados.

| Aspecto | Definición en el esquema actual |
|---|---|
| Equipos de un partido | `PARTIDOS_EQUIPOS` identifica cada participante mediante partido y equipo. `Condicion_local` distingue los dos lados. Las consultas de local y visitante pasan por esta tabla. |
| Entrenadores | `ENTRENADORES` guarda la identidad. `ENTRENADORES_PARTIDO` asigna el entrenador al equipo en ese encuentro. |
| Jornada y fecha | `PARTIDOS` conserva `Ronda` y exige `Fecha_hora_utc`. El total de rondas de la liga y el estado del partido quedaron fuera del esquema según el acuerdo del piloto. |
| Temporada | `LIGAS` conserva la temporada y su ID externo. Separar competición y temporada sigue siendo una [propuesta](otros/IDEAS_FUTURAS.md). |
| Estadísticas | Cada fila de equipo corresponde a un partido, equipo y período. Cada fila individual corresponde a un partido y jugador y se vincula con su alineación. |

Al cambiar una entidad, actualizar la fila correspondiente con el acuerdo que motivó el cambio y el módulo que lo implementa. Mantener los diccionarios originales como referencia histórica.

## Diseño original

Las siguientes definiciones conservan los atributos, tipos y relaciones del diseño inicial. Para consultas sobre la implementación, utiliza el diccionario SQLite vigente.

### Catálogos y partidos

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

### Estadísticas de jugadores

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

### Estadísticas de partidos

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

### Relaciones originales

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

### Evolución prevista para Fases 2 y 3 (Fuera del Piloto Actual)

El esquema vigente de 11 tablas cubre íntegramente la recolección deportiva de la **Fase 1**. Para soportar las etapas predictivas y de ejecución auditada se proyectan las siguientes extensiones:

| Tabla proyectada | Fase | Propósito | Clave y relación principal |
| :--- | :--- | :--- | :--- |
| **`CUOTAS_PREPARTIDO`** | Fase 2 | Almacenar cuotas capturadas por mercado y línea para calcular probabilidad implícita y Valor Esperado ($EV$). | PK: `(Id_cuota)` · FK: `(Id_partido)` $\rightarrow$ `PARTIDOS` |
| **`BITACORA_APUESTAS`** | Fase 3 | Registrar cada apuesta ejecutada, monto apostado (*stake*), probabilidad estimada, resultado y retorno neto para auditoría del *bankroll*. | PK: `(Id_apuesta)` · FK: `(Id_partido)` $\rightarrow$ `PARTIDOS` |