import os

from etl.schema_explorer import elegir_carpeta, explorar_carpeta
from scrapers.match_crawler import run_url_explorer
from scrapers.stats_scraper import procesar_archivo_ronda

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_FOLDER = os.path.join(BASE_DIR, "data", "urls_league_rounds")

def mostrar_menu():
    print("\n" + "=" * 45)
    print("  ORÁCULO - MOTOR DE RECOLECCIÓN")
    print("=" * 45)
    print("  1. Ejecutar Explorador de URLs (Etapa 1)")
    print("  2. Extraer Estadísticas y Alineaciones (Etapa 2)")
    print("  3. Explorar esquemas de JSON")
    print("  0. Salir del sistema")
    print("=" * 45)

def seleccionar_archivo_ronda():
    """Permite elegir el archivo de URLs que procesará el scraper."""
    if not os.path.exists(INPUT_FOLDER):
        print("\nLa carpeta de datos no existe aún. Ejecuta la Etapa 1 primero.")
        return None

    archivos = sorted(
        archivo for archivo in os.listdir(INPUT_FOLDER) if archivo.endswith(".json")
    )

    if not archivos:
        print("\nNo hay archivos JSON disponibles. Ejecuta la Etapa 1 primero.")
        return None

    print("\nArchivos disponibles:")
    for indice, archivo in enumerate(archivos, start=1):
        print(f"  {indice}. {archivo}")
    print("  c. Cancelar y volver al menú principal")

    seleccion = input(
        f"\nElige el archivo a procesar (1-{len(archivos)}): "
    ).strip().lower()

    if seleccion == "c":
        return None

    try:
        indice = int(seleccion) - 1
        return archivos[indice]
    except (ValueError, IndexError):
        print("\nEntrada inválida. Debes ingresar un número dentro del rango.")
        return None


def main():
    while True:
        mostrar_menu()
        opcion = input("\nSelecciona una opción (0-3): ").strip()

        if opcion == "1":
            print("\nIniciando Explorador de URLs...")
            run_url_explorer()

        elif opcion == "2":
            print("\nPreparando extracción de estadísticas y alineaciones...")
            archivo_elegido = seleccionar_archivo_ronda()

            if archivo_elegido:
                print(f"\nEjecutando Etapa 2 para: {archivo_elegido}")
                procesar_archivo_ronda(archivo_elegido)

        elif opcion == "3":
            print("\nExplorador de esquemas JSON")
            carpeta_elegida = elegir_carpeta()
            explorar_carpeta(carpeta_elegida)

        elif opcion == "0":
            print("\nCerrando Oráculo. ¡Hasta pronto!\n")
            break

        else:
            print("\nOpción no válida. Por favor, selecciona 0, 1, 2 o 3.")


if __name__ == "__main__":
    main()