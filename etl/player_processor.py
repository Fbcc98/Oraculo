"""Normalizacion de los JSON almacenados en ``data/players_stats``."""

from etl.common import Common


PLAYER_STATS_MAP = {
    "minutesPlayed": ("Minutos_jugados", Common.entero),
    "rating": ("Rating", Common.decimal),
    "goals": ("Goles", Common.entero),
    "goalAssist": ("Asistencias", Common.entero),
    "expectedGoals": ("Goles_esperados_xG", Common.decimal),
    "expectedAssists": ("Asistencias_esperadas_xA", Common.decimal),
    "expectedGoalsOnTarget": ("Goles_esperados_al_arco_xGOT", Common.decimal),
    "totalShots": ("Remates", Common.entero),
    "onTargetScoringAttempt": ("Remates_arco", Common.entero),
    "shotOffTarget": ("Remates_fuera", Common.entero),
    "blockedScoringAttempt": ("Remates_bloqueados", Common.entero),
    "hitWoodwork": ("Tiros_al_palo", Common.entero),
    "bigChanceCreated": ("Grandes_ocasiones_creadas", Common.entero),
    "bigChanceMissed": ("Grandes_ocasiones_falladas", Common.entero),
    "totalPass": ("Pases", Common.entero), "accuratePass": ("Pases_precisos", Common.entero),
    "keyPass": ("Pases_clave", Common.entero),
    "totalOwnHalfPasses": ("Pases_campo_propio", Common.entero),
    "accurateOwnHalfPasses": ("Pases_precisos_campo_propio", Common.entero),
    "totalOppositionHalfPasses": ("Pases_campo_rival", Common.entero),
    "accurateOppositionHalfPasses": ("Pases_precisos_campo_rival", Common.entero),
    "totalLongBalls": ("Balones_largos", Common.entero),
    "accurateLongBalls": ("Balones_largos_precisos", Common.entero),
    "totalCross": ("Centros", Common.entero), "accurateCross": ("Centros_precisos", Common.entero),
    "totalContest": ("Regates", Common.entero), "wonContest": ("Regates_ganados", Common.entero),
    "duelWon": ("Duelos_ganados", Common.entero), "duelLost": ("Duelos_perdidos", Common.entero),
    "aerialWon": ("Duelos_aereos_ganados", Common.entero),
    "aerialLost": ("Duelos_aereos_perdidos", Common.entero),
    "totalTackle": ("Entradas", Common.entero), "wonTackle": ("Entradas_ganadas", Common.entero),
    "interceptionWon": ("Intercepciones", Common.entero), "ballRecovery": ("Recuperaciones", Common.entero),
    "totalClearance": ("Despejes", Common.entero), "outfielderBlock": ("Bloqueos", Common.entero),
    "fouls": ("Faltas_cometidas", Common.entero), "wasFouled": ("Faltas_recibidas", Common.entero),
    "totalOffside": ("Fueras_de_juego", Common.entero),
    "possessionLostCtrl": ("Perdidas_posesion", Common.entero),
    "dispossessed": ("Desposesiones", Common.entero), "unsuccessfulTouch": ("Controles_fallidos", Common.entero),
    "touches": ("Toques", Common.entero), "ballCarriesCount": ("Conducciones_balon", Common.entero),
    "totalBallCarriesDistance": ("Distancia_conduccion_balon", Common.decimal),
    "progressiveBallCarriesCount": ("Conducciones_progresivas", Common.entero),
    "totalProgressiveBallCarriesDistance": ("Distancia_conduccion_progresiva", Common.decimal),
    "totalProgression": ("Progresion_total", Common.decimal),
    "bestBallCarryProgression": ("Mejor_progresion_conduccion", Common.decimal),
    "kilometersCovered": ("Distancia_recorrida_km", Common.decimal), "topSpeed": ("Velocidad_maxima", Common.decimal),
    "numberOfSprints": ("Sprints", Common.entero),
    "metersCoveredRunningKm": ("Distancia_corriendo_km", Common.decimal),
    "metersCoveredHighSpeedRunningKm": ("Distancia_alta_velocidad_km", Common.decimal),
    "metersCoveredSprintingKm": ("Distancia_sprint_km", Common.decimal),
    "challengeLost": ("Desafios_perdidos", Common.entero), "clearanceOffLine": ("Despejes_linea_gol", Common.entero),
    "lastManTackle": ("Entradas_ultimo_hombre", Common.entero),
    "errorLeadToAShot": ("Errores_terminan_remate", Common.entero),
    "errorLeadToAGoal": ("Errores_terminan_gol", Common.entero),
    "ownGoals": ("Autogoles", Common.entero), "penaltyConceded": ("Penales_cometidos", Common.entero),
    "penaltyWon": ("Penales_recibidos", Common.entero), "saves": ("Atajadas", Common.entero),
    "savedShotsFromInsideTheBox": ("Atajadas_dentro_area", Common.entero),
    "totalKeeperSweeper": ("Salidas_portero", Common.entero),
    "accurateKeeperSweeper": ("Salidas_portero_precisas", Common.entero),
    "goodHighClaim": ("Centros_altos_atrapados", Common.entero), "punches": ("Despejes_punos", Common.entero),
    "penaltyFaced": ("Penales_enfrentados", Common.entero),
    "keeperSaveValue": ("Valor_atajadas_portero", Common.decimal), "goalsPrevented": ("Goles_evitados", Common.decimal),
}


class PlayerProcessor:
    @staticmethod
    def _color_primario(color):
        """Extrae el color hexadecimal principal informado por Sofascore."""
        if isinstance(color, dict):
            return color.get("primary")
        return color

    def procesar(self, json_data, id_partido, id_equipo_local, id_equipo_visita):
        resultado = {"jugadores": [], "alineaciones": [], "estadisticas": [], "partidos_equipos": []}
        resultado["alineacion_confirmada"] = Common.booleano(json_data.get("confirmed"))
        equipos_vistos = set()
        jugadores_vistos = set()

        for condicion in ("home", "away"):
            bloque_equipo = json_data.get(condicion) or {}
            id_equipo = id_equipo_local if condicion == "home" else id_equipo_visita
            if id_equipo not in equipos_vistos:
                resultado["partidos_equipos"].append({
                    "Id_partido": id_partido, "Id_equipo": id_equipo,
                    "Condicion_local": condicion == "home",
                    "Formacion": bloque_equipo.get("formation"),
                    "Color_jugadores": self._color_primario(
                        bloque_equipo.get("playerColor")
                    ),
                    "Color_portero": self._color_primario(
                        bloque_equipo.get("goalkeeperColor")
                    ),
                })
                equipos_vistos.add(id_equipo)

            for entrada in bloque_equipo.get("players") or []:
                jugador = entrada.get("player") or {}
                id_jugador = Common.entero(jugador.get("id"))
                if id_jugador is None or id_equipo is None:
                    continue

                if id_jugador not in jugadores_vistos:
                    pais = jugador.get("country") or {}
                    resultado["jugadores"].append({
                        "Id_jugador": id_jugador,
                        "Pais_codigo_alpha3": pais.get("alpha3"),
                        "Pais_nombre": pais.get("name"),
                        "Nombre_jugador": jugador.get("name"),
                        "Nombre_corto": jugador.get("shortName"),
                        "Slug": jugador.get("slug"),
                        "Estatura_cm": Common.entero(jugador.get("height")),
                        "Fecha_nacimiento": Common.fecha_desde_timestamp(jugador.get("dateOfBirthTimestamp")),
                        "Genero": jugador.get("gender"),
                        "Posicion_principal": jugador.get("position"),
                    })
                    jugadores_vistos.add(id_jugador)

                resultado["alineaciones"].append({
                    "Id_partido": id_partido, "Id_jugador": id_jugador, "Id_equipo": id_equipo,
                    "Es_titular": not bool(entrada.get("substitute")),
                    "Posicion_partido": entrada.get("position"),
                    "Dorsal": Common.entero(entrada.get("shirtNumber") or entrada.get("jerseyNumber")),
                })

                stats_origen = entrada.get("statistics")
                if stats_origen:
                    stats = {"Id_partido": id_partido, "Id_jugador": id_jugador, "Id_equipo": id_equipo}
                    for clave, (columna, conversor) in PLAYER_STATS_MAP.items():
                        if clave in stats_origen:
                            stats[columna] = conversor(stats_origen.get(clave))
                    versiones = stats_origen.get("ratingVersions") or {}
                    if "original" in versiones:
                        stats["Rating_original"] = Common.decimal(versiones.get("original"))
                    if "alternative" in versiones:
                        stats["Rating_alternativo"] = Common.decimal(versiones.get("alternative"))
                    resultado["estadisticas"].append(stats)
        return resultado


def procesar_jugadores(json_data, id_partido, id_equipo_local, id_equipo_visita):
    return PlayerProcessor().procesar(
        json_data, id_partido, id_equipo_local, id_equipo_visita
    )
