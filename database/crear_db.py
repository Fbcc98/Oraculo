import sqlite3
import os

def crear_base_datos():

    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DB_PATH = os.path.join(BASE_DIR, "database", "oraculo.database")

    conexion = sqlite3.connect(DB_PATH)
    cursor = conexion.cursor()

    print("Conectado a la base de datos oraculo.database")

    query_crear_tabla = """
    
    CREATE TABLE IF NOT EXISTS PAIS (
        Id_pais TINYINT PRIMARY KEY,
        Nombre_pais VARCHAR(20) NOT NULL
    );
        
    CREATE TABLE IF NOT EXISTS LIGAS (
        Id_liga SMALLINT PRIMARY KEY,
        Nombre_liga VARCHAR(20) NOT NULL,
        Rondas TINYINT NOT NULL,
        Temporada VARCHAR(5) NOT NULL,
        Id_pais TINYINT NOT NULL,
        FOREIGN KEY (Id_pais) REFERENCES PAIS (Id_pais)
    );
        
    CREATE TABLE IF NOT EXISTS EQUIPOS (
        Id_equipo TINYINT PRIMARY KEY,
        Nombre_equipo VARCHAR(20) NOT NULL,
        Id_liga SMALLINT NOT NULL,
        Id_pais TINYINT NOT NULL,
        FOREIGN KEY (Id_liga) REFERENCES LIGAS (Id_liga),
        FOREIGN KEY (Id_pais) REFERENCES PAIS (Id_pais)
    );
      
    CREATE TABLE IF NOT EXISTS PARTIDOS (
       Id_partido INTEGER PRIMARY KEY,
       Id_liga SMALLINT NOT NULL,
       Id_equipo_visita SMALLINT NOT NULL,
       Id_equipo_local SMALLINT NOT NULL,
       Fecha DATE NOT NULL,
       Goles_visita SMALLINT NOT NULL,
       Goles_local SMALLINT NOT NULL,
       Url TEXT NOT NULL, 
       FOREIGN KEY (Id_liga) REFERENCES LIGAS (Id_liga),
       FOREIGN KEY (Id_equipo_visita) REFERENCES EQUIPOS (Id_equipo),
       FOREIGN KEY (Id_equipo_local) REFERENCES EQUIPOS (Id_equipo) 
    );
    
    CREATE TABLE IF NOT EXISTS PARTIDOS_ESTADISTICAS(
        Id_partido INTEGER NOT NULL,
        Id_equipo INTEGER NOT NULL,
        Periodo VARCHAR(10) NOT NULL,
        Condicion_local BOOLEAN NOT NULL,
        Posesion_balon DECIMAL,
        Distancia_recorrida_km DECIMAL,
        Goles_esperados_xG DECIMAL,
        Grandes_ocasiones TINYINT,
        Sprints SMALLINT,
        Corners TINYINT,
        Faltas TINYINT,
        Pases SMALLINT,
        Entradas TINYINT,
        Tiros_libres TINYINT,
        Tarjetas_amarillas TINYINT,
        Tarjetas_rojas TINYINT,
        Remates TINYINT,
        Tiros_arco TINYINT,
        Tiros_al_palo TINYINT,
        Tiros_fuera TINYINT,
        Tiros_bloqueados TINYINT,
        Tiros_adentro_del_area TINYINT,
        Tiros_afuera_del_area TINYINT,
        Ocasiones_claras_realizadas TINYINT,
        Ocasiones_claras_falladas TINYINT,
        Toques_dentro_del_area TINYINT,
        Faltas_recibidas_ultima_tercio TINYINT,
        Fueras_de_juego TINYINT,
        Pases_precisos SMALLINT,
        Saques_de_banda TINYINT,
        Pases_al_ultimo_tercio SMALLINT,
        Total_pases_area_penal_adversaria SMALLINT,
        Total_pases_precisos_area_penal_adversaria SMALLINT,
        Total_balones_largos SMALLINT,
        Total_balones_largos_precisos SMALLINT,
        Total_centros TINYINT,
        Total_centros_exitosos TINYINT,
        Porcentaje_duelos_ganados DECIMAL,
        Balones_perdidos TINYINT,
        Total_duelos_suelo SMALLINT,
        Total_duelos_suelo_ganados SMALLINT,
        Total_duelos_aereos SMALLINT,
        Total_duelos_aereos_ganados SMALLINT,
        Total_regates TINYINT,
        Total_regates_ganados TINYINT,
        Total_entradas TINYINT,
        Total_entradas_ganadas TINYINT,
        Porcentaje_entradas_ganadas DECIMAL,
        Intercepciones TINYINT,
        Recuperaciones TINYINT,
        Despejes TINYINT,
        Errores_terminan_tiro TINYINT,
        Errores_terminan_gol TINYINT,
        Atajadas TINYINT,
        Goles_evitados DECIMAL,
        Grandes_atajadas TINYINT,
        Balones_aereos_atrapados TINYINT,
        Despejes_punos TINYINT,
        Saques_de_arco TINYINT,
        PRIMARY KEY (Id_partido, Id_equipo, Periodo),
        FOREIGN KEY (Id_partido) REFERENCES PARTIDOS (Id_partido),
        FOREIGN KEY (Id_equipo) REFERENCES EQUIPOS (Id_equipo)
     );    
    """

    try:
        cursor.executescript(query_crear_tabla)
        conexion.commit()
        print("¡El ecosistema de tablas fue creado con éxito!")
    except sqlite3.Error as e:
        print(f"Error al crear la tabla: {e}")

if __name__ == "__main__":
    crear_base_datos()