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
