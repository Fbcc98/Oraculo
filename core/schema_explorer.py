import json
import os

def explorar_estadisticas_json(ruta_carpeta_jsons):
    """
    Recorre todos los archivos JSON en una carpeta y extrae
    todos los grupos y 'keys' de estadísticas únicos en TODOS los periodos.
    """
    grupos_unicos = set()
    estadisticas_unicas = set()

    # Recorremos todos los archivos en la carpeta especificada
    for nombre_archivo in os.listdir(ruta_carpeta_jsons):
        if nombre_archivo.endswith('.json'):
            ruta_completa = os.path.join(ruta_carpeta_jsons, nombre_archivo)

            with open(ruta_completa, 'r', encoding='utf-8') as f:
                try:
                    data = json.load(f)

                    # Buscamos la llave statistics de forma segura con .get()
                    for periodo in data.get('statistics', []):

                        # ELIMINAMOS el filtro de 'ALL'. Revisamos todo.
                        for grupo in periodo.get('groups', []):
                            grupos_unicos.add(grupo.get('groupName'))

                            for stat in grupo.get('statisticsItems', []):
                                # CAMBIO CLAVE: Extraemos el 'key' (para el código) y el 'name' (para tu lectura)
                                key = stat.get('key')
                                name = stat.get('name')

                                # Guardamos ambos en el set para que la impresión sea útil
                                estadisticas_unicas.add(f"Key: '{key}' -> Name: '{name}'")

                except Exception as e:
                    print(f"Error leyendo {nombre_archivo}: {e}")

    return grupos_unicos, estadisticas_unicas


if __name__ == '__main__':
    # 1. Le decimos a Python que busque la raíz del proyecto
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # 2. Armamos la ruta blindada concatenando la raíz con 'data' y 'matchs_stats'
    CARPETA_DATOS = os.path.join(BASE_DIR, "data", "matchs_stats")

    print("Iniciando escaneo masivo de JSONs...")
    print(f"Buscando en la ruta exacta: {CARPETA_DATOS}")

    # Ejecutamos la función
    grupos, stats = explorar_estadisticas_json(CARPETA_DATOS)

    # Solo imprimimos si encontró algo
    if grupos or stats:
        print("\n" + "=" * 50)
        print(f"🔍 GRUPOS ENCONTRADOS ({len(grupos)}):")
        print("=" * 50)
        for g in sorted(grupos):
            print(f" - {g}")

        print("\n" + "=" * 50)
        print(f"📊 ESTADÍSTICAS ÚNICAS ENCONTRADAS ({len(stats)}):")
        print("=" * 50)
        for s in sorted(stats):
            print(f" - {s}")
    else:
        print("\n⚠️ No se encontraron estadísticas. Revisa la ruta o los archivos JSON.")