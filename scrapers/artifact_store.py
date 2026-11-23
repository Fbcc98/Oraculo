"""Contratos de JSON crudo, persistencia atómica y auditoría sin navegador."""

import json
import logging
import os
from pathlib import Path
import re
import tempfile


ARTEFACTOS = {
    "stats": ("matchs_stats", "statistics"),
    "lineups": ("players_stats", "home"),
    "managers": ("managers", "homeManager"),
}


def eventos_validos(datos):
    return isinstance(datos, dict) and isinstance(datos.get("events"), list)


def artefacto_valido(datos, tipo):
    """Exige raíz esperada, tipo correcto y contenido no vacío."""
    if not isinstance(datos, dict):
        return False
    if tipo == "stats":
        return isinstance(datos.get("statistics"), list) and bool(datos["statistics"])
    if tipo == "lineups":
        return isinstance(datos.get("home"), dict) and bool(datos["home"])
    if tipo == "managers":
        return any(
            isinstance(datos.get(clave), dict) and bool(datos[clave])
            for clave in ("homeManager", "awayManager")
        )
    raise ValueError(f"Artefacto desconocido: {tipo}")


def leer_json(ruta):
    with open(ruta, encoding="utf-8") as archivo:
        return json.load(archivo)


def archivo_valido(ruta, tipo):
    try:
        return artefacto_valido(leer_json(ruta), tipo)
    except (OSError, ValueError, UnicodeError):
        return False


def guardar_json_atomico(datos, ruta):
    """Reemplaza un archivo solo tras completar la serialización temporal."""
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    temporal = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=ruta.parent,
            prefix=f".{ruta.name}.", suffix=".tmp", delete=False,
        ) as archivo:
            temporal = Path(archivo.name)
            json.dump(datos, archivo, ensure_ascii=False, indent=2)
        os.replace(temporal, ruta)
    finally:
        if temporal is not None:
            temporal.unlink(missing_ok=True)


def rutas_artefactos(raw_dir, liga, ronda, partido_id):
    liga = liga.replace(" ", "_").replace("/", "_").replace("\\", "_")
    return {
        tipo: Path(raw_dir) / carpeta / f"{tipo}_{liga}_R{ronda}_{partido_id}.json"
        for tipo, (carpeta, _) in ARTEFACTOS.items()
    }


def ids_finalizados(datos):
    """Si hay un homólogo inválido se aborta; nunca se omite el filtro en silencio."""
    if not eventos_validos(datos):
        raise ValueError("El JSON de eventos debe contener 'events' como lista.")
    return {
        str(evento["id"])
        for evento in datos["events"]
        if isinstance(evento, dict) and evento.get("id") is not None
        and isinstance(evento.get("status"), dict)
        and evento["status"].get("type") == "finished"
    }


def inspeccionar_ronda(ruta_urls, raw_dir=None, solo_ids=None):
    """Inspecciona URLs únicas por ID, estado y faltantes sin crear archivos."""
    ruta_urls = Path(ruta_urls)
    raw_dir = Path(raw_dir) if raw_dir is not None else ruta_urls.parent.parent
    datos = leer_json(ruta_urls)
    if not isinstance(datos, dict) or not isinstance(datos.get("urls"), list):
        raise ValueError(f"{ruta_urls} debe contener una lista 'urls'.")
    liga, ronda = datos["liga"], datos["ronda"]
    nombre_eventos = ruta_urls.name.replace("urls_", "round_events_", 1)
    ruta_eventos = raw_dir / "league_events" / nombre_eventos
    finalizados = (
        ids_finalizados(leer_json(ruta_eventos)) if ruta_eventos.exists() else None
    )
    if finalizados is None:
        logging.warning(
            "Sin eventos homólogos para %s; no se filtra estado.", ruta_urls.name
        )
    seleccion = None if solo_ids is None else {str(pid) for pid in solo_ids}
    partidos, vistos = [], set()
    for url in datos["urls"]:
        coincidencia = (
            re.search(r"#id:([1-9][0-9]*)$", url) if isinstance(url, str) else None
        )
        if coincidencia is None:
            raise ValueError(f"URL sin ID de partido válido: {url!r}")
        pid = coincidencia.group(1)
        if pid in vistos or (seleccion is not None and pid not in seleccion):
            continue
        vistos.add(pid)
        rutas = rutas_artefactos(raw_dir, liga, ronda, pid)
        partidos.append({
            "partido_id": pid, "url": url, "rutas": rutas,
            "finalizado": finalizados is None or pid in finalizados,
            "faltantes": [
                tipo for tipo, ruta in rutas.items()
                if not archivo_valido(ruta, tipo)
            ],
        })
    return partidos


def pendiente(partido):
    return {clave: partido[clave] for clave in ("partido_id", "url", "faltantes")}


def resumen_ronda(partidos):
    """Los contadores son disjuntos; completos cuenta descargas de esta ejecución."""
    return {
        "total": len(partidos),
        "completos": 0,
        "omitidos_existentes": sum(
            p["finalizado"] and not p["faltantes"] for p in partidos
        ),
        "omitidos_no_finalizados": sum(not p["finalizado"] for p in partidos),
        "incompletos": [
            pendiente(p) for p in partidos if p["finalizado"] and p["faltantes"]
        ],
    }


def reportar_resumen(resumen, etiqueta):
    logging.info(
        "%s: total=%s, completos=%s, omitidos existentes=%s, "
        "omitidos no finalizados=%s, incompletos=%s",
        etiqueta, resumen["total"], resumen["completos"],
        resumen["omitidos_existentes"], resumen["omitidos_no_finalizados"],
        len(resumen["incompletos"]),
    )
    for item in resumen["incompletos"]:
        logging.warning(
            "Partido %s | %s | faltantes: %s", item["partido_id"],
            item["url"], ", ".join(item["faltantes"]),
        )


def auditar_archivo_ronda(ruta_urls, raw_dir=None):
    resumen = resumen_ronda(inspeccionar_ronda(ruta_urls, raw_dir))
    reportar_resumen(resumen, str(ruta_urls))
    return resumen
