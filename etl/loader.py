"""Carga transaccional de estructuras normalizadas en SQLite."""

import sqlite3

from database.crear_db import DB_PATH, crear_base_datos


ORDEN_CARGA = (
    "PAIS",
    "LIGAS",
    "EQUIPOS",
    "JUGADORES",
    "ENTRENADORES",
    "PARTIDOS",
    "PARTIDOS_EQUIPOS",
    "ENTRENADORES_PARTIDO",
    "ALINEACION",
    "PARTIDOS_ESTADISTICAS",
    "JUGADORES_ESTADISTICAS",
)

CLAVES_CONFLICTO = {
    "PAIS": ("Id_pais",),
    "LIGAS": ("Id_liga",),
    "EQUIPOS": ("Id_equipo",),
    "JUGADORES": ("Id_jugador",),
    "ENTRENADORES": ("Id_entrenador",),
    "PARTIDOS": ("Id_partido",),
    "PARTIDOS_EQUIPOS": ("Id_partido", "Id_equipo"),
    "ENTRENADORES_PARTIDO": ("Id_partido", "Id_equipo"),
    "ALINEACION": ("Id_partido", "Id_jugador"),
    "PARTIDOS_ESTADISTICAS": ("Id_partido", "Id_equipo", "Periodo"),
    "JUGADORES_ESTADISTICAS": ("Id_partido", "Id_jugador"),
}


class Loader:
    """Persiste un lote completo o entidades individuales mediante UPSERT."""

    def __init__(self, db_path=DB_PATH, inicializar=True):
        self.db_path = db_path
        if inicializar:
            crear_base_datos(db_path)

    def conectar(self):
        conexion = sqlite3.connect(self.db_path)
        conexion.row_factory = sqlite3.Row
        conexion.execute("PRAGMA foreign_keys = ON")
        return conexion

    @staticmethod
    def _lista(valor):
        if valor is None:
            return []
        return valor if isinstance(valor, list) else [valor]

    @staticmethod
    def _columnas_tabla(conexion, tabla):
        return {fila[1] for fila in conexion.execute(f'PRAGMA table_info("{tabla}")')}

    def _upsert(self, conexion, tabla, registro):
        if tabla not in CLAVES_CONFLICTO:
            raise ValueError(f"Tabla no permitida para carga: {tabla}")
        if not registro:
            return

        columnas_validas = self._columnas_tabla(conexion, tabla)
        desconocidas = set(registro) - columnas_validas
        if desconocidas:
            raise ValueError(
                f"Columnas desconocidas para {tabla}: {', '.join(sorted(desconocidas))}"
            )

        columnas = list(registro)
        claves = CLAVES_CONFLICTO[tabla]
        faltantes = set(claves) - set(columnas)
        if faltantes:
            raise ValueError(
                f"Faltan claves de {tabla}: {', '.join(sorted(faltantes))}"
            )

        nombres = ", ".join(f'"{columna}"' for columna in columnas)
        parametros = ", ".join("?" for _ in columnas)
        conflicto = ", ".join(f'"{clave}"' for clave in claves)
        actualizables = [columna for columna in columnas if columna not in claves]
        if actualizables:
            actualizacion = ", ".join(
                f'"{columna}" = excluded."{columna}"' for columna in actualizables
            )
            accion = f"DO UPDATE SET {actualizacion}"
        else:
            accion = "DO NOTHING"

        conexion.execute(
            f'INSERT INTO "{tabla}" ({nombres}) VALUES ({parametros}) '
            f"ON CONFLICT ({conflicto}) {accion}",
            [registro[columna] for columna in columnas],
        )

    def _resolver_pais_jugador(self, conexion, jugador):
        """Convierte los datos auxiliares del país en la FK ``Id_pais``."""
        registro = dict(jugador)
        codigo = registro.pop("Pais_codigo_alpha3", None)
        nombre = registro.pop("Pais_nombre", None)
        if registro.get("Id_pais") is not None or (not codigo and not nombre):
            return registro

        fila = None
        if codigo:
            fila = conexion.execute(
                "SELECT Id_pais FROM PAIS WHERE Codigo_alpha3 = ?", (codigo,)
            ).fetchone()
        if fila is None and nombre:
            fila = conexion.execute(
                "SELECT Id_pais FROM PAIS WHERE Nombre_pais = ?", (nombre,)
            ).fetchone()

        if fila is None:
            cursor = conexion.execute(
                "INSERT INTO PAIS (Codigo_alpha3, Nombre_pais) VALUES (?, ?)",
                (codigo, nombre or codigo),
            )
            registro["Id_pais"] = cursor.lastrowid
        else:
            registro["Id_pais"] = fila["Id_pais"]
        return registro

    def _cargar_en_conexion(self, conexion, datos):
        cantidades = {tabla: 0 for tabla in ORDEN_CARGA}
        for tabla in ORDEN_CARGA:
            for registro_original in self._lista(datos.get(tabla)):
                registro = dict(registro_original)
                if tabla == "JUGADORES":
                    registro = self._resolver_pais_jugador(conexion, registro)
                self._upsert(conexion, tabla, registro)
                cantidades[tabla] += 1
        return cantidades

    def cargar(self, datos):
        """Carga un diccionario por tablas dentro de una sola transacción."""
        with self.conectar() as conexion:
            return self._cargar_en_conexion(conexion, datos)

    def cargar_partido(
        self, paises, liga, equipos, partido, datos_match,
        datos_player=None, datos_manager=None, partidos_equipos=None,
    ):
        """Combina entidades maestras y resultados de los procesadores ETL."""
        datos_player = datos_player or {}
        datos_manager = datos_manager or {}
        partidos = self._lista(partido)
        if len(partidos) != 1:
            raise ValueError("cargar_partido requiere exactamente un registro PARTIDOS")
        datos = {
            "PAIS": self._lista(paises),
            "LIGAS": self._lista(liga),
            "EQUIPOS": self._lista(equipos),
            "JUGADORES": datos_player.get("jugadores", []),
            "ENTRENADORES": datos_manager.get("entrenadores", []),
            "PARTIDOS": partidos,
            "PARTIDOS_EQUIPOS": partidos_equipos
            if partidos_equipos is not None
            else datos_player.get("partidos_equipos", []),
            "ENTRENADORES_PARTIDO": datos_manager.get(
                "entrenadores_partido", []
            ),
            "ALINEACION": datos_player.get("alineaciones", []),
            "PARTIDOS_ESTADISTICAS": datos_match or [],
            "JUGADORES_ESTADISTICAS": datos_player.get("estadisticas", []),
        }

        if "alineacion_confirmada" in datos_player:
            datos["PARTIDOS"][0] = dict(datos["PARTIDOS"][0])
            datos["PARTIDOS"][0]["Alineacion_confirmada"] = datos_player[
                "alineacion_confirmada"
            ]
        return self.cargar(datos)
