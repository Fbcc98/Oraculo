"""Normalizacion de los JSON almacenados en ``data/matchs_stats``."""

from etl.common import Common


# key de Sofascore: (columna normalizada, tipo de conversion, fuente)
ESTADISTICAS_SIMPLES = {
    "ballPossession": ("Posesion_balon", "porcentaje", "display"),
    "kilometersCovered": ("Distancia_recorrida_km", "decimal", "value"),
    "expectedGoals": ("Goles_esperados_xG", "decimal", "value"),
    "bigChanceCreated": ("Grandes_ocasiones", "entero", "value"),
    "numberOfSprints": ("Sprints", "entero", "value"),
    "cornerKicks": ("Corners", "entero", "value"),
    "fouls": ("Faltas", "entero", "value"),
    "passes": ("Pases", "entero", "value"),
    "totalTackle": ("Entradas", "entero", "value"),
    "freeKicks": ("Tiros_libres", "entero", "value"),
    "yellowCards": ("Tarjetas_amarillas", "entero", "value"),
    "redCards": ("Tarjetas_rojas", "entero", "value"),
    "totalShotsOnGoal": ("Remates", "entero", "value"),
    "shotsOnGoal": ("Tiros_arco", "entero", "value"),
    "hitWoodwork": ("Tiros_al_palo", "entero", "value"),
    "shotsOffGoal": ("Tiros_fuera", "entero", "value"),
    "blockedScoringAttempt": ("Tiros_bloqueados", "entero", "value"),
    "totalShotsInsideBox": ("Tiros_adentro_del_area", "entero", "value"),
    "totalShotsOutsideBox": ("Tiros_afuera_del_area", "entero", "value"),
    "bigChanceScored": ("Ocasiones_claras_realizadas", "entero", "value"),
    "bigChanceMissed": ("Ocasiones_claras_falladas", "entero", "value"),
    "touchesInOppBox": ("Toques_dentro_del_area", "entero", "value"),
    "fouledFinalThird": ("Faltas_recibidas_ultimo_tercio", "entero", "value"),
    "offsides": ("Fueras_de_juego", "entero", "value"),
    "accuratePasses": ("Pases_precisos", "entero", "value"),
    "throwIns": ("Saques_de_banda", "entero", "value"),
    "finalThirdEntries": ("Entradas_ultimo_tercio", "entero", "value"),
    "duelWonPercent": ("Porcentaje_duelos_ganados", "porcentaje", "display"),
    "dispossessed": ("Balones_perdidos", "entero", "value"),
    "interceptionWon": ("Intercepciones", "entero", "value"),
    "ballRecovery": ("Recuperaciones", "entero", "value"),
    "totalClearance": ("Despejes", "entero", "value"),
    "errorsLeadToShot": ("Errores_terminan_tiro", "entero", "value"),
    "errorsLeadToGoal": ("Errores_terminan_gol", "entero", "value"),
    "goalkeeperSaves": ("Atajadas", "entero", "value"),
    "goalsPrevented": ("Goles_evitados", "decimal", "value"),
    "diveSaves": ("Grandes_atajadas", "entero", "value"),
    "highClaims": ("Balones_aereos_atrapados", "entero", "value"),
    "punches": ("Despejes_punos", "entero", "value"),
    "goalKicks": ("Saques_de_arco", "entero", "value"),
}

ESTADISTICAS_COMPUESTAS = {
    "finalThirdPhaseStatistic": (
        ("Total_pases_area_penal_adversaria", "total"),
        ("Pases_precisos_area_penal_adversaria", "value"),
    ),
    "accurateLongBalls": (
        ("Total_balones_largos", "total"),
        ("Balones_largos_precisos", "value"),
    ),
    "accurateCross": (("Total_centros", "total"), ("Centros_exitosos", "value")),
    "groundDuelsPercentage": (
        ("Total_duelos_suelo", "total"),
        ("Duelos_suelo_ganados", "value"),
    ),
    "aerialDuelsPercentage": (
        ("Total_duelos_aereos", "total"),
        ("Duelos_aereos_ganados", "value"),
    ),
    "dribblesPercentage": (("Total_regates", "total"), ("Regates_ganados", "value")),
    "wonTacklePercent": (("Total_entradas", "total"), ("Entradas_ganadas", "value")),
}


class MatchProcessor:
    @staticmethod
    def _evento(json_data):
        """Acepta un evento directo o una respuesta envuelta en ``event``."""
        if not isinstance(json_data, dict):
            raise ValueError("El evento debe ser un objeto JSON")
        evento = json_data.get("event", json_data)
        if not isinstance(evento, dict):
            raise ValueError("La respuesta no contiene un objeto event válido")
        return evento

    @staticmethod
    def _marcador_final(score):
        """Obtiene el marcador mostrado sin convertir ausencias en cero."""
        if not isinstance(score, dict):
            return None
        for campo in ("display", "current", "normaltime"):
            valor = Common.entero(score.get(campo))
            if valor is not None:
                return valor
        return None

    @staticmethod
    def _url_evento(evento):
        slug = evento.get("slug")
        custom_id = evento.get("customId")
        event_id = Common.entero(evento.get("id"))
        if not slug or not custom_id or event_id is None:
            return None
        return (
            f"https://www.sofascore.com/football/match/{slug}/"
            f"{custom_id}#id:{event_id}"
        )

    def procesar_evento(self, json_data, id_liga, url=None):
        """Normaliza exclusivamente los metadatos acordados de un partido finalizado."""
        evento = self._evento(json_data)
        estado = (evento.get("status") or {}).get("type")
        if estado != "finished":
            raise ValueError(
                f"El evento {evento.get('id')} no está finalizado: {estado!r}"
            )

        home_team = evento.get("homeTeam") or {}
        away_team = evento.get("awayTeam") or {}
        event_id = Common.entero(evento.get("id"))
        home_team_id = Common.entero(home_team.get("id"))
        away_team_id = Common.entero(away_team.get("id"))
        fecha_hora_utc = Common.fecha_hora_desde_timestamp(
            evento.get("startTimestamp")
        )

        faltantes = []
        if event_id is None:
            faltantes.append("event.id")
        if home_team_id is None:
            faltantes.append("homeTeam.id")
        if away_team_id is None:
            faltantes.append("awayTeam.id")
        if fecha_hora_utc is None:
            faltantes.append("startTimestamp")
        if faltantes:
            raise ValueError(
                "Faltan identificadores o fecha obligatorios: "
                + ", ".join(faltantes)
            )

        partido = {
            "Id_partido": event_id,
            "Id_liga": Common.entero(id_liga),
            "Fecha_hora_utc": fecha_hora_utc,
            "Ronda": Common.entero((evento.get("roundInfo") or {}).get("round")),
            "Goles_local": self._marcador_final(evento.get("homeScore")),
            "Goles_visita": self._marcador_final(evento.get("awayScore")),
            "Url": url or self._url_evento(evento),
        }
        equipos = [
            {
                "Id_equipo": home_team_id,
                "Nombre_equipo": home_team.get("name"),
                "Slug": home_team.get("slug"),
            },
            {
                "Id_equipo": away_team_id,
                "Nombre_equipo": away_team.get("name"),
                "Slug": away_team.get("slug"),
            },
        ]
        partidos_equipos = [
            {
                "Id_partido": event_id,
                "Id_equipo": home_team_id,
                "Condicion_local": True,
            },
            {
                "Id_partido": event_id,
                "Id_equipo": away_team_id,
                "Condicion_local": False,
            },
        ]
        return {
            "partido": partido,
            "equipos": equipos,
            "partidos_equipos": partidos_equipos,
            "id_equipo_local": home_team_id,
            "id_equipo_visita": away_team_id,
        }

    def procesar_eventos_total(self, json_data, id_liga, ronda=None, urls=None):
        """Deduplica y normaliza los eventos finalizados de team-events/total."""
        raiz = (json_data or {}).get("tournamentTeamEvents")
        if not isinstance(raiz, dict):
            raise ValueError("El JSON no contiene tournamentTeamEvents")

        eventos_unicos = {}
        for grupo in raiz.values():
            if not isinstance(grupo, dict):
                continue
            for eventos_equipo in grupo.values():
                if not isinstance(eventos_equipo, list):
                    continue
                for evento in eventos_equipo:
                    if not isinstance(evento, dict):
                        continue
                    event_id = Common.entero(evento.get("id"))
                    if event_id is not None:
                        eventos_unicos.setdefault(event_id, evento)

        ronda_objetivo = Common.entero(ronda)
        urls = urls or {}
        normalizados = []
        for event_id, evento in eventos_unicos.items():
            if (evento.get("status") or {}).get("type") != "finished":
                continue
            event_round = Common.entero(
                (evento.get("roundInfo") or {}).get("round")
            )
            if ronda_objetivo is not None and event_round != ronda_objetivo:
                continue
            normalizados.append(
                self.procesar_evento(
                    evento,
                    id_liga,
                    url=urls.get(event_id),
                )
            )
        return normalizados

    @staticmethod
    def _valor(item, condicion, fuente):
        sufijo = "home" if condicion == "local" else "away"
        if fuente == "display":
            return item.get(sufijo)
        return item.get(f"{sufijo}{fuente.title()}")

    @staticmethod
    def _convertir(valor, tipo):
        return getattr(Common, tipo)(valor)

    def procesar(self, json_data, id_partido, id_equipo_local, id_equipo_visita):
        registros = []
        for bloque in json_data.get("statistics") or []:
            periodo = bloque.get("period")
            por_equipo = {
                "local": {"Id_partido": id_partido, "Id_equipo": id_equipo_local, "Periodo": periodo},
                "visita": {"Id_partido": id_partido, "Id_equipo": id_equipo_visita, "Periodo": periodo},
            }
            for grupo in bloque.get("groups") or []:
                for item in grupo.get("statisticsItems") or []:
                    clave = item.get("key")
                    simple = ESTADISTICAS_SIMPLES.get(clave)
                    for condicion, registro in por_equipo.items():
                        if simple:
                            columna, tipo, fuente = simple
                            valor = self._valor(item, condicion, fuente)
                            registro[columna] = self._convertir(valor, tipo)
                        for columna, fuente in ESTADISTICAS_COMPUESTAS.get(clave, ()):
                            valor = self._valor(item, condicion, fuente)
                            registro[columna] = Common.entero(valor)
            registros.extend((por_equipo["local"], por_equipo["visita"]))
        return registros


def procesar_estadisticas_partido(json_data, id_partido, id_equipo_local, id_equipo_visita):
    """Interfaz funcional conservada para facilitar la migracion gradual."""
    return MatchProcessor().procesar(json_data, id_partido, id_equipo_local, id_equipo_visita)
