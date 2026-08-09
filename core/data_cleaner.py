import json

def limpiar_valor(valor_str, tipo_dato):
    """
    Limpia los valores que vienen como texto en el JSON para convertirlos en números puros.
    """
    if not isinstance(valor_str, str):
        return valor_str

    valor_str = valor_str.strip()

    try:
        if tipo_dato == 'porcentaje':
            return float(valor_str.replace('%', '')) / 100.0
        elif tipo_dato == 'distancia':
            return float(valor_str.replace('km', '').strip())
        elif tipo_dato == 'float':
            return float(valor_str)
        elif tipo_dato == 'int':
            return int(valor_str)
        else:
            return valor_str
    except ValueError:
        return 0  # Valor por defecto en caso de que venga un "-" o esté vacío


def procesar_estadisticas_partido(json_data, id_partido, id_equipo_local, id_equipo_visita):

    estadisticas_db = []

    # Recorremos los distintos períodos (ALL, 1ST, 2ST)
    for periodo_data in json_data.get('statistics', []):
        periodo = periodo_data.get('period')

        # Diccionarios base para almacenar las stats de este período
        stats_local = {'Id_partido': id_partido, 'Id_equipo': id_equipo_local, 'Periodo': periodo}
        stats_visita = {'Id_partido': id_partido, 'Id_equipo': id_equipo_visita, 'Periodo': periodo}

        # Iteramos sobre los grupos de estadísticas (Match overview, etc.)
        for grupo in periodo_data.get('groups', []):
            for item in grupo.get('statisticsItems', []):
                nombre_stat = item.get('key')

                if nombre_stat == 'ballPossession':
                    stats_local['Posesion_balon'] = limpiar_valor(item.get('home'), 'porcentaje')
                    stats_visita['Posesion_balon'] = limpiar_valor(item.get('away'), 'porcentaje')

                elif nombre_stat == 'kilometersCovered':
                    stats_local['Distancia_recorrida_km'] = float(item.get('homeValue', 0))
                    stats_visita['Distancia_recorrida_km'] = float(item.get('awayValue', 0))

                elif nombre_stat == 'expectedGoals':
                    stats_local['Goles_esperados_xG'] = float(item.get('homeValue', 0))
                    stats_visita['Goles_esperados_xG'] = float(item.get('awayValue', 0))

                elif nombre_stat == 'bigChanceCreated':
                    stats_local['Grandes_ocasiones'] = int(item.get('homeValue', 0))
                    stats_visita['Grandes_ocasiones'] = int(item.get('awayValue', 0))

                elif nombre_stat == 'numberOfSprints':
                    stats_local['Sprints'] = int(item.get('homeValue', 0))
                    stats_visita['Sprints'] = int(item.get('awayValue', 0))

                elif nombre_stat == 'cornerKicks':
                    stats_local['Corners'] = int(item.get('homeValue', 0))
                    stats_visita['Corners'] = int(item.get('awayValue', 0))

                elif nombre_stat == 'fouls':
                    stats_local['Faltas'] = int(item.get('homeValue', 0))
                    stats_visita['Faltas'] = int(item.get('awayValue', 0))

                elif nombre_stat == 'passes':
                    stats_local['Pases'] = int(item.get('homeValue', 0))
                    stats_visita['Pases'] = int(item.get('awayValue', 0))

                elif nombre_stat == 'totalTackle':
                    stats_local['Entradas'] = int(item.get('homeValue', 0))
                    stats_visita['Entradas'] = int(item.get('awayValue', 0))

                elif nombre_stat == 'totalShotsOnGoal':
                    stats_local['Remates'] = int(item.get('homeValue', 0))
                    stats_visita['Remates'] = int(item.get('awayValue', 0))

                elif nombre_stat == 'freeKicks':
                    stats_local['Tiros_libres'] = int(item.get('homeValue', 0))
                    stats_visita['Tiros_libres'] = int(item.get('awayValue', 0))

                elif nombre_stat == 'yellowCards':
                    stats_local['Tarjetas_amarillas'] = int(item.get('homeValue', 0))
                    stats_visita['Tarjetas_amarillas'] = int(item.get('awayValue', 0))

                elif nombre_stat == 'redCards':
                    stats_local['Tarjetas_rojas'] = int(item.get('homeValue', 0))
                    stats_visita['Tarjetas_rojas'] = int(item.get('awayValue', 0))

                elif nombre_stat == 'totalShotsOnGoal':
                    stats_local['Remates'] = int(item.get('homeValue', 0))
                    stats_visita['Remates'] = int(item.get('awayValue', 0))

                elif nombre_stat == 'shotsOnGoal':
                    stats_local['Tiros_arco'] = int(item.get('homeValue', 0))
                    stats_visita['Tiros_arco'] = int(item.get('awayValue', 0))

                elif nombre_stat == 'hitWoodwork':
                    stats_local['Tiros_al_palo'] = int(item.get('homeValue', 0))
                    stats_visita['Tiros_al_palo'] = int(item.get('awayValue', 0))

                elif nombre_stat == 'shotsOffGoal':
                    stats_local['Tiros_fuera'] = int(item.get('homeValue', 0))
                    stats_visita['Tiros_fuera'] = int(item.get('awayValue', 0))

                elif nombre_stat == 'blockedScoringAttempt':
                    stats_local['Tiros_bloqueados'] = int(item.get('homeValue', 0))
                    stats_visita['Tiros_bloqueados'] = int(item.get('awayValue', 0))

                elif nombre_stat == 'totalShotsInsideBox':
                    stats_local['Tiros_adentro_del_area'] = int(item.get('homeValue', 0))
                    stats_visita['Tiros_adentro_del_area'] = int(item.get('awayValue', 0))

                elif nombre_stat == 'totalShotsOutsideBox':
                    stats_local['Tiros_afuera_del_area'] = int(item.get('homeValue', 0))
                    stats_visita['Tiros_afuera_del_area'] = int(item.get('awayValue', 0))

                elif nombre_stat == 'bigChanceScored':
                    stats_local['Ocasiones_claras_realizadas'] = int(item.get('homeValue', 0))
                    stats_visita['Ocasiones_claras_realizadas'] = int(item.get('awayValue', 0))

                elif nombre_stat == 'bigChanceMissed':
                    stats_local['Ocasiones_claras_falladas'] = int(item.get('homeValue', 0))
                    stats_visita['Ocasiones_claras_falladas'] = int(item.get('awayValue', 0))

                elif nombre_stat == 'accurateThroughBall':
                    stats_local['Pases_filtrados'] = int(item.get('homeValue', 0))
                    stats_visita['Pases_filtrados'] = int(item.get('awayValue', 0))

                elif nombre_stat == 'touchesInOppBox':
                    stats_local['Toques_dentro_del_area'] = int(item.get('homeValue', 0))
                    stats_visita['Toques_dentro_del_area'] = int(item.get('awayValue', 0))

                elif nombre_stat == 'fouledFinalThird':
                    stats_local['Faltas_recibidas_ultima_tercio'] = int(item.get('homeValue', 0))
                    stats_visita['Faltas_recibidas_ultima_tercio'] = int(item.get('awayValue', 0))

                elif nombre_stat == 'offsides':
                    stats_local['Fueras_de_juego'] = int(item.get('homeValue', 0))
                    stats_visita['Fueras_de_juego'] = int(item.get('awayValue', 0))

                elif nombre_stat == 'accuratePasses':
                    stats_local['Pases_precisos'] = int(item.get('homeValue', 0))
                    stats_visita['Pases_precisos'] = int(item.get('awayValue', 0))

                elif nombre_stat == 'throwIns':
                    stats_local['Saques_banda'] = int(item.get('homeValue', 0))
                    stats_visita['Saques_banda'] = int(item.get('awayValue', 0))

                elif nombre_stat == 'finalThirdEntries':
                    stats_local['Pases_al_ultimo_tercio'] = int(item.get('homeValue', 0))
                    stats_visita['Pases_al_ultimo_tercio'] = int(item.get('awayValue', 0))

                elif nombre_stat == 'finalThirdPhaseStatistic':
                    stats_local['Total_pases_area_penal_adversaria'] = int(item.get('homeTotal', 0))
                    stats_visita['Total_pases_area_penal_adversaria'] = int(item.get('awayTotal', 0))

                elif nombre_stat == 'finalThirdPhaseStatistic':
                    stats_local['Total_pases_precisos_area_penal_adversaria'] = int(item.get('homeValue', 0))
                    stats_visita['Total_pases_precisos_area_penal_adversaria'] = int(item.get('awayValue', 0))

                elif nombre_stat == 'accurateLongBalls':
                    stats_local['Total_balones_largos'] = int(item.get('homeTotal', 0))
                    stats_visita['Total_balones_largos'] = int(item.get('awayTotal', 0))

                elif nombre_stat == 'accurateLongBalls':
                    stats_local['Total_balones_largos_precisos'] = int(item.get('homeValue', 0))
                    stats_visita['Total_balones_largos_precisos'] = int(item.get('awayValue', 0))

                elif nombre_stat == 'accurateCross':
                    stats_local['Total_centros'] = int(item.get('homeTotal', 0))
                    stats_visita['Total_centros'] = int(item.get('awayTotal', 0))

                elif nombre_stat == 'accurateCross':
                    stats_local['Total_centros_exitosos'] = int(item.get('homeValue', 0))
                    stats_visita['Total_centros_exitosos'] = int(item.get('awayValue', 0))

                elif nombre_stat == 'duelWonPercent':
                    stats_local['Porcentaje_duelos_ganados'] = limpiar_valor(item.get('home'), 'porcentaje')
                    stats_visita['Porcentaje_duelos_ganados'] = limpiar_valor(item.get('away'), 'porcentaje')

                elif nombre_stat == 'dispossessed':
                    stats_local['Balones_perdidos'] = int(item.get('homeValue', 0))
                    stats_visita['Balones_perdidos'] = int(item.get('awayValue', 0))

                elif nombre_stat == 'groundDuelsPercentage':
                    stats_local['Total_duelos_suelo'] = int(item.get('homeTotal', 0))
                    stats_visita['Total_duelos_suelo'] = int(item.get('awayTotal', 0))

                elif nombre_stat == 'groundDuelsPercentage':
                    stats_local['Total_duelos_suelo_ganados'] = int(item.get('homeValue', 0))
                    stats_visita['Total_duelos_suelo_ganados'] = int(item.get('awayValue', 0))

                elif nombre_stat == 'aerialDuelsPercentage':
                    stats_local['Total_duelos_aereos'] = int(item.get('homeTotal', 0))
                    stats_visita['Total_duelos_aereos'] = int(item.get('awayTotal', 0))

                elif nombre_stat == 'aerialDuelsPercentage':
                    stats_local['Total_duelos_aereos_ganados'] = int(item.get('homeValue', 0))
                    stats_visita['Total_duelos_aereos_ganados'] = int(item.get('awayValue', 0))

                elif nombre_stat == 'dribblesPercentage':
                    stats_local['Total_regates'] = int(item.get('homeTotal', 0))
                    stats_visita['Total_regates'] = int(item.get('awayTotal', 0))

                elif nombre_stat == 'dribblesPercentage':
                    stats_local['Total_regates_ganados'] = int(item.get('homeValue', 0))
                    stats_visita['Total_regates_ganados'] = int(item.get('awayValue', 0))

                elif nombre_stat == 'totalTackle':
                    stats_local['Total_entradas'] = int(item.get('homeValue', 0))
                    stats_visita['Total_entradas'] = int(item.get('awayValue', 0))

                elif nombre_stat == 'wonTacklePercent':
                    stats_local['Total_entradas_ganadas'] = int(item.get('homeValue', 0))
                    stats_visita['Total_entradas_ganadas'] = int(item.get('awayValue', 0))

                elif nombre_stat == 'wonTacklePercent':
                    stats_local['Porcentaje_entradas_ganadas'] = limpiar_valor(item.get('home'), 'porcentaje')
                    stats_visita['Porcentaje_entradas_ganadas'] = limpiar_valor(item.get('away'), 'porcentaje')

                elif nombre_stat == 'interceptionWon':
                    stats_local['Intercepciones'] = int(item.get('homeValue', 0))
                    stats_visita['Intercepciones'] = int(item.get('awayValue', 0))

                elif nombre_stat == 'ballRecovery':
                    stats_local['Recuperaciones'] = int(item.get('homeValue', 0))
                    stats_visita['Recuperaciones'] = int(item.get('awayValue', 0))

                elif nombre_stat == 'totalClearance':
                    stats_local['Despejes'] = int(item.get('homeValue', 0))
                    stats_visita['Despejes'] = int(item.get('awayValue', 0))

                elif nombre_stat == 'errorsLeadToShot':
                    stats_local['Errores_terminan_tiro'] = int(item.get('homeValue', 0))
                    stats_visita['Errores_terminan_tiro'] = int(item.get('awayValue', 0))

                elif nombre_stat == 'goalkeeperSaves':
                    stats_local['Atajadas'] = int(item.get('homeValue', 0))
                    stats_visita['Atajadas'] = int(item.get('awayValue', 0))

                elif nombre_stat == 'goalsPrevented':
                    stats_local['Goles_evitados'] = float(item.get('homeValue', 0))
                    stats_visita['Goles_evitados'] = float(item.get('awayValue', 0))

                elif nombre_stat == 'diveSaves':
                    stats_local['Grandes_atajadas'] = int(item.get('homeValue', 0))
                    stats_visita['Grandes_atajadas'] = int(item.get('awayValue', 0))

                elif nombre_stat == 'highClaims':
                    stats_local['Balones_aereos_atrapados'] = int(item.get('homeValue', 0))
                    stats_visita['Balones_aereos_atrapados'] = int(item.get('awayValue', 0))

                elif nombre_stat == 'punches':
                    stats_local['Despejes_punos'] = int(item.get('homeValue', 0))
                    stats_visita['Despejes_punos'] = int(item.get('awayValue', 0))

                elif nombre_stat == 'goalKicks':
                    stats_local['Saques_de_arco'] = int(item.get('homeValue', 0))
                    stats_visita['Saques_de_arco'] = int(item.get('awayValue', 0))

        estadisticas_db.append(stats_local)
        estadisticas_db.append(stats_visita)

    return estadisticas_db