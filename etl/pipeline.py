"""Orquestacion del flujo JSON -> normalizacion -> SQLite."""

import json
import sqlite3
from os import PathLike

from etl.loader import Loader
from etl.manager_processor import ManagerProcessor
from etl.match_processor import MatchProcessor
from etl.player_processor import PlayerProcessor


class PipelineError(ValueError):
    """Error de contexto o entrada antes de iniciar la carga."""


class Pipeline:
    """Coordina procesadores y cargador sin mezclar sus responsabilidades."""

    CAMPOS_CONTEXTO = {
        "paises", "liga", "equipos", "partido",
        "id_equipo_local", "id_equipo_visita",
    }

    def __init__(
        self,
        loader=None,
        match_processor=None,
        player_processor=None,
        manager_processor=None,
    ):
        self.loader = loader or Loader()
        self.match_processor = match_processor or MatchProcessor()
        self.player_processor = player_processor or PlayerProcessor()
        self.manager_processor = manager_processor or ManagerProcessor()

    @staticmethod
    def leer_json(origen):
        """Acepta un diccionario JSON o una ruta a un archivo JSON."""
        if isinstance(origen, dict):
            return origen
        if isinstance(origen, (str, bytes, PathLike)):
            try:
                with open(origen, "r", encoding="utf-8") as archivo:
                    contenido = json.load(archivo)
            except (OSError, json.JSONDecodeError) as error:
                raise PipelineError(f"No fue posible leer {origen}: {error}") from error
            if not isinstance(contenido, dict):
                raise PipelineError(f"El JSON debe contener un objeto: {origen}")
            return contenido
        raise PipelineError("El origen debe ser un diccionario o una ruta JSON")

    @classmethod
    def validar_contexto(cls, contexto):
        if not isinstance(contexto, dict):
            raise PipelineError("El contexto del partido debe ser un diccionario")
        faltantes = [campo for campo in cls.CAMPOS_CONTEXTO if contexto.get(campo) is None]
        if faltantes:
            raise PipelineError(
                "Faltan datos obligatorios del contexto: " + ", ".join(sorted(faltantes))
            )
        partido = contexto["partido"]
        if not isinstance(partido, dict) or partido.get("Id_partido") is None:
            raise PipelineError("partido debe incluir Id_partido")
        ids_equipos = {equipo.get("Id_equipo") for equipo in contexto["equipos"]}
        esperados = {contexto["id_equipo_local"], contexto["id_equipo_visita"]}
        if None in ids_equipos or not esperados.issubset(ids_equipos):
            raise PipelineError("equipos debe contener los equipos local y visitante")

    @staticmethod
    def _relaciones_basicas(contexto):
        id_partido = contexto["partido"]["Id_partido"]
        return [
            {"Id_partido": id_partido, "Id_equipo": contexto["id_equipo_local"],
             "Condicion_local": True},
            {"Id_partido": id_partido, "Id_equipo": contexto["id_equipo_visita"],
             "Condicion_local": False},
        ]

    def procesar_partido(
        self,
        contexto,
        match_json,
        player_json=None,
        manager_json=None,
    ):
        """Normaliza y carga atomicamente un partido completo o parcial."""
        self.validar_contexto(contexto)
        match_data = self.leer_json(match_json)
        player_data = self.leer_json(player_json) if player_json is not None else None
        manager_data = (
            self.leer_json(manager_json) if manager_json is not None else None
        )
        id_partido = contexto["partido"]["Id_partido"]
        id_local = contexto["id_equipo_local"]
        id_visita = contexto["id_equipo_visita"]

        estadisticas_partido = self.match_processor.procesar(
            match_data, id_partido, id_local, id_visita
        )
        if not estadisticas_partido:
            raise PipelineError(f"No se encontraron estadisticas para {id_partido}")

        datos_jugadores = None
        datos_managers = None
        relaciones = contexto.get("partidos_equipos")
        if player_data is not None:
            datos_jugadores = self.player_processor.procesar(
                player_data, id_partido, id_local, id_visita
            )
            relaciones = relaciones or datos_jugadores["partidos_equipos"]
        if manager_data is not None:
            datos_managers = self.manager_processor.procesar(
                manager_data,
                id_partido,
                id_local,
                id_visita,
            )
        relaciones = relaciones or self._relaciones_basicas(contexto)

        cantidades = self.loader.cargar_partido(
            paises=contexto["paises"], liga=contexto["liga"],
            equipos=contexto["equipos"], partido=contexto["partido"],
            datos_match=estadisticas_partido, datos_player=datos_jugadores,
            datos_manager=datos_managers, partidos_equipos=relaciones,
        )
        return {"Id_partido": id_partido, "cargados": cantidades}

    def procesar_lote(self, casos, continuar_con_error=False):
        """Procesa casos independientes y devuelve resultados y errores."""
        resultado = {"procesados": [], "errores": []}
        for caso in casos:
            try:
                resultado["procesados"].append(self.procesar_partido(
                    caso["contexto"],
                    caso["match_json"],
                    caso.get("player_json"),
                    caso.get("manager_json"),
                ))
            except (KeyError, ValueError, sqlite3.Error) as error:
                if not continuar_con_error:
                    raise
                resultado["errores"].append({"caso": caso, "error": str(error)})
        return resultado
