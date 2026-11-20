"""Normalización del JSON de managers asociado a un partido de Sofascore."""

from etl.common import Common


class ManagerProcessor:
    """Normaliza entrenadores principales sin depender del esquema persistente."""

    LADOS = (
        ("homeManager", "local"),
        ("awayManager", "visita"),
    )

    @staticmethod
    def _id_equipo(condicion, id_equipo_local, id_equipo_visita):
        return id_equipo_local if condicion == "local" else id_equipo_visita

    def procesar(
        self,
        json_data,
        id_partido,
        id_equipo_local,
        id_equipo_visita,
    ):
        """Devuelve los managers disponibles asociados al partido y equipo."""
        if not isinstance(json_data, dict):
            raise ValueError("El JSON de managers debe ser un objeto")

        partido_id = Common.entero(id_partido)
        equipo_local_id = Common.entero(id_equipo_local)
        equipo_visita_id = Common.entero(id_equipo_visita)
        if partido_id is None:
            raise ValueError("id_partido es obligatorio para procesar managers")
        if equipo_local_id is None or equipo_visita_id is None:
            raise ValueError(
                "Los identificadores de los equipos local y visitante son obligatorios"
            )

        entrenadores = []
        entrenadores_partido = []
        for campo, condicion in self.LADOS:
            manager = json_data.get(campo)
            if manager is None:
                continue
            if not isinstance(manager, dict):
                raise ValueError(f"{campo} debe ser un objeto o null")

            manager_id = Common.entero(manager.get("id"))
            if manager_id is None:
                raise ValueError(f"{campo}.id es obligatorio cuando existe el manager")

            entrenadores.append(
                {
                    "Id_entrenador": manager_id,
                    "Nombre_entrenador": manager.get("name"),
                    "Nombre_corto": manager.get("shortName"),
                    "Slug": manager.get("slug"),
                }
            )
            entrenadores_partido.append(
                {
                    "Id_partido": partido_id,
                    "Id_equipo": self._id_equipo(
                        condicion,
                        equipo_local_id,
                        equipo_visita_id,
                    ),
                    "Id_entrenador": manager_id,
                }
            )

        return {
            "entrenadores": entrenadores,
            "entrenadores_partido": entrenadores_partido,
        }


def procesar_managers(
    json_data,
    id_partido,
    id_equipo_local,
    id_equipo_visita,
):
    """Interfaz funcional para facilitar su uso desde el Pipeline."""
    return ManagerProcessor().procesar(
        json_data,
        id_partido,
        id_equipo_local,
        id_equipo_visita,
    )
