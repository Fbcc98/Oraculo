"""Creacion del esquema relacional de Oraculo en SQLite."""

import os
import sqlite3

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "database", "oraculo.db")

MATCH_INTEGER_COLUMNS = """Grandes_ocasiones Sprints Corners Faltas Pases Entradas Tiros_libres
Tarjetas_amarillas Tarjetas_rojas Remates Tiros_arco Tiros_al_palo Tiros_fuera Tiros_bloqueados
Tiros_adentro_del_area Tiros_afuera_del_area Ocasiones_claras_realizadas Ocasiones_claras_falladas
Toques_dentro_del_area Faltas_recibidas_ultimo_tercio Fueras_de_juego Pases_precisos Saques_de_banda
Entradas_ultimo_tercio Total_pases_area_penal_adversaria Pases_precisos_area_penal_adversaria
Total_balones_largos Balones_largos_precisos Total_centros Centros_exitosos Balones_perdidos
Total_duelos_suelo Duelos_suelo_ganados Total_duelos_aereos Duelos_aereos_ganados Total_regates
Regates_ganados Total_entradas Entradas_ganadas Intercepciones Recuperaciones Despejes
Errores_terminan_tiro Errores_terminan_gol Atajadas Grandes_atajadas Balones_aereos_atrapados
Despejes_punos Saques_de_arco""".split()

MATCH_REAL_COLUMNS = """Posesion_balon Distancia_recorrida_km Goles_esperados_xG
Porcentaje_duelos_ganados Goles_evitados""".split()

PLAYER_INTEGER_COLUMNS = """Minutos_jugados Goles Asistencias Remates Remates_arco Remates_fuera
Remates_bloqueados Tiros_al_palo Grandes_ocasiones_creadas Grandes_ocasiones_falladas Pases
Pases_precisos Pases_clave Pases_campo_propio Pases_precisos_campo_propio Pases_campo_rival
Pases_precisos_campo_rival Balones_largos Balones_largos_precisos Centros Centros_precisos Regates
Regates_ganados Duelos_ganados Duelos_perdidos Duelos_aereos_ganados Duelos_aereos_perdidos
Entradas Entradas_ganadas Intercepciones Recuperaciones Despejes Bloqueos Faltas_cometidas
Faltas_recibidas Fueras_de_juego Perdidas_posesion Desposesiones Controles_fallidos Toques
Conducciones_balon Conducciones_progresivas Sprints Desafios_perdidos Despejes_linea_gol
Entradas_ultimo_hombre Errores_terminan_remate Errores_terminan_gol Autogoles Penales_cometidos
Penales_recibidos Atajadas Atajadas_dentro_area Salidas_portero Salidas_portero_precisas
Centros_altos_atrapados Despejes_punos Penales_enfrentados""".split()

PLAYER_REAL_COLUMNS = """Rating Goles_esperados_xG Asistencias_esperadas_xA
Goles_esperados_al_arco_xGOT Distancia_conduccion_balon Distancia_conduccion_progresiva
Progresion_total Mejor_progresion_conduccion Distancia_recorrida_km Velocidad_maxima
Distancia_corriendo_km Distancia_alta_velocidad_km Distancia_sprint_km Valor_atajadas_portero
Goles_evitados Rating_original Rating_alternativo""".split()


def _columnas(nombres, tipo):
    return ",\n        ".join(f"{nombre} {tipo}" for nombre in nombres)


SCHEMA_SQL = f"""
CREATE TABLE IF NOT EXISTS PAIS (
    Id_pais INTEGER PRIMARY KEY, Codigo_alpha3 TEXT UNIQUE,
    Nombre_pais TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS LIGAS (
    Id_liga INTEGER PRIMARY KEY, Id_pais INTEGER NOT NULL, Nombre_liga TEXT NOT NULL,
    Id_temporada_externo INTEGER NOT NULL UNIQUE, Temporada TEXT NOT NULL,
    FOREIGN KEY (Id_pais) REFERENCES PAIS(Id_pais) ON UPDATE CASCADE ON DELETE RESTRICT
);
CREATE TABLE IF NOT EXISTS EQUIPOS (
    Id_equipo INTEGER PRIMARY KEY, Id_pais INTEGER, Nombre_equipo TEXT NOT NULL, Slug TEXT,
    FOREIGN KEY (Id_pais) REFERENCES PAIS(Id_pais) ON UPDATE CASCADE ON DELETE SET NULL
);
CREATE TABLE IF NOT EXISTS JUGADORES (
    Id_jugador INTEGER PRIMARY KEY, Id_pais INTEGER, Nombre_jugador TEXT NOT NULL,
    Nombre_corto TEXT, Slug TEXT, Estatura_cm INTEGER, Fecha_nacimiento TEXT,
    Genero TEXT, Posicion_principal TEXT,
    FOREIGN KEY (Id_pais) REFERENCES PAIS(Id_pais) ON UPDATE CASCADE ON DELETE SET NULL
);
CREATE TABLE IF NOT EXISTS ENTRENADORES (
    Id_entrenador INTEGER PRIMARY KEY, Nombre_entrenador TEXT NOT NULL,
    Nombre_corto TEXT, Slug TEXT
);
CREATE TABLE IF NOT EXISTS PARTIDOS (
    Id_partido INTEGER PRIMARY KEY, Id_liga INTEGER NOT NULL, Fecha_hora_utc TEXT NOT NULL,
    Ronda INTEGER, Goles_local INTEGER, Goles_visita INTEGER,
    Url TEXT NOT NULL UNIQUE, Alineacion_confirmada INTEGER NOT NULL DEFAULT 0,
    CHECK (Alineacion_confirmada IN (0,1)),
    FOREIGN KEY (Id_liga) REFERENCES LIGAS(Id_liga) ON UPDATE CASCADE ON DELETE RESTRICT
);
CREATE TABLE IF NOT EXISTS PARTIDOS_EQUIPOS (
    Id_partido INTEGER NOT NULL, Id_equipo INTEGER NOT NULL, Condicion_local INTEGER NOT NULL,
    Formacion TEXT, Color_jugadores TEXT, Color_portero TEXT,
    PRIMARY KEY (Id_partido, Id_equipo), UNIQUE (Id_partido, Condicion_local),
    CHECK (Condicion_local IN (0,1)),
    FOREIGN KEY (Id_partido) REFERENCES PARTIDOS(Id_partido) ON UPDATE CASCADE ON DELETE CASCADE,
    FOREIGN KEY (Id_equipo) REFERENCES EQUIPOS(Id_equipo) ON UPDATE CASCADE ON DELETE RESTRICT
);
CREATE TABLE IF NOT EXISTS ENTRENADORES_PARTIDO (
    Id_partido INTEGER NOT NULL, Id_equipo INTEGER NOT NULL, Id_entrenador INTEGER NOT NULL,
    PRIMARY KEY (Id_partido, Id_equipo),
    FOREIGN KEY (Id_partido,Id_equipo) REFERENCES PARTIDOS_EQUIPOS(Id_partido,Id_equipo)
        ON UPDATE CASCADE ON DELETE CASCADE,
    FOREIGN KEY (Id_entrenador) REFERENCES ENTRENADORES(Id_entrenador)
        ON UPDATE CASCADE ON DELETE RESTRICT
);
CREATE TABLE IF NOT EXISTS ALINEACION (
    Id_partido INTEGER NOT NULL, Id_jugador INTEGER NOT NULL, Id_equipo INTEGER NOT NULL,
    Es_titular INTEGER NOT NULL, Posicion_partido TEXT, Dorsal INTEGER,
    PRIMARY KEY (Id_partido, Id_jugador), CHECK (Es_titular IN (0,1)),
    FOREIGN KEY (Id_partido,Id_equipo) REFERENCES PARTIDOS_EQUIPOS(Id_partido,Id_equipo)
        ON UPDATE CASCADE ON DELETE CASCADE,
    FOREIGN KEY (Id_jugador) REFERENCES JUGADORES(Id_jugador) ON UPDATE CASCADE ON DELETE RESTRICT
);
CREATE TABLE IF NOT EXISTS PARTIDOS_ESTADISTICAS (
    Id_partido INTEGER NOT NULL, Id_equipo INTEGER NOT NULL, Periodo TEXT NOT NULL,
    {_columnas(MATCH_INTEGER_COLUMNS, 'INTEGER')},
    {_columnas(MATCH_REAL_COLUMNS, 'REAL')},
    PRIMARY KEY (Id_partido,Id_equipo,Periodo),
    FOREIGN KEY (Id_partido,Id_equipo) REFERENCES PARTIDOS_EQUIPOS(Id_partido,Id_equipo)
        ON UPDATE CASCADE ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS JUGADORES_ESTADISTICAS (
    Id_partido INTEGER NOT NULL, Id_jugador INTEGER NOT NULL, Id_equipo INTEGER NOT NULL,
    {_columnas(PLAYER_INTEGER_COLUMNS, 'INTEGER')},
    {_columnas(PLAYER_REAL_COLUMNS, 'REAL')},
    PRIMARY KEY (Id_partido,Id_jugador),
    FOREIGN KEY (Id_partido,Id_jugador) REFERENCES ALINEACION(Id_partido,Id_jugador)
        ON UPDATE CASCADE ON DELETE CASCADE,
    FOREIGN KEY (Id_partido,Id_equipo) REFERENCES PARTIDOS_EQUIPOS(Id_partido,Id_equipo)
        ON UPDATE CASCADE ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_partidos_liga_fecha ON PARTIDOS(Id_liga,Fecha_hora_utc);
CREATE INDEX IF NOT EXISTS idx_alineacion_equipo ON ALINEACION(Id_equipo);
CREATE INDEX IF NOT EXISTS idx_entrenadores_partido_entrenador
    ON ENTRENADORES_PARTIDO(Id_entrenador,Id_partido);
CREATE INDEX IF NOT EXISTS idx_partido_stats_equipo ON PARTIDOS_ESTADISTICAS(Id_equipo,Id_partido);
CREATE INDEX IF NOT EXISTS idx_jugador_stats_equipo ON JUGADORES_ESTADISTICAS(Id_equipo,Id_partido);
"""


def _preparar_esquema(conexion):
    """Retira el esquema legado solo cuando todas sus tablas estan vacias."""
    tablas = {
        fila[0]
        for fila in conexion.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'"
        )
    }
    if not tablas:
        return

    columnas_partidos = (
        {fila[1] for fila in conexion.execute("PRAGMA table_info(PARTIDOS)")}
        if "PARTIDOS" in tablas
        else set()
    )
    columnas_ligas = (
        {fila[1] for fila in conexion.execute("PRAGMA table_info(LIGAS)")}
        if "LIGAS" in tablas
        else set()
    )
    requiere_reconstruccion = (
        ("PARTIDOS" in tablas and "Fecha_hora_utc" not in columnas_partidos)
        or "Estado_partido" in columnas_partidos
        or "Rondas" in columnas_ligas
    )
    if not requiere_reconstruccion:
        return

    tablas_con_datos = [
        tabla
        for tabla in tablas
        if conexion.execute(f'SELECT EXISTS(SELECT 1 FROM "{tabla}" LIMIT 1)').fetchone()[0]
    ]
    if tablas_con_datos:
        raise sqlite3.DatabaseError(
            "Se detecto un esquema antiguo con datos. No se modifico la base: "
            + ", ".join(sorted(tablas_con_datos))
        )

    orden_eliminacion = (
        "JUGADORES_ESTADISTICAS", "PARTIDOS_ESTADISTICAS", "ALINEACION",
        "ENTRENADORES_PARTIDO", "PARTIDOS_EQUIPOS", "PARTIDOS",
        "ENTRENADORES", "JUGADORES", "EQUIPOS", "LIGAS", "PAIS",
    )
    for tabla in orden_eliminacion:
        if tabla in tablas:
            conexion.execute(f'DROP TABLE "{tabla}"')


def crear_base_datos(db_path=DB_PATH):
    """Crea las tablas faltantes sin borrar datos existentes."""
    os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
    try:
        with sqlite3.connect(db_path) as conexion:
            conexion.execute("PRAGMA foreign_keys = ON")
            _preparar_esquema(conexion)
            conexion.executescript(SCHEMA_SQL)
            if conexion.execute("PRAGMA foreign_keys").fetchone()[0] != 1:
                raise sqlite3.DatabaseError("No fue posible activar las claves foraneas")
        print(f"Base de datos inicializada correctamente: {db_path}")
    except sqlite3.Error as error:
        print(f"Error al crear la base de datos: {error}")
        raise


if __name__ == "__main__":
    crear_base_datos()
