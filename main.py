import os
from scrapers.script_rounds import run_url_explorer
from scrapers.script_match_stats import procesar_archivo_ronda

# Configuramos la ruta hacia la carpeta donde se guardan tus JSON
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_FOLDER = os.path.join(BASE_DIR, 'data', 'urls_league_rounds')

def mostrar_menu():
    print("\n" + "=" * 45)
    print(" 🔮 ORÁCULO - MOTOR DE RECOLECCIÓN 🔮")
    print("=" * 45)
    print("  1. 🌐 Ejecutar Explorador de URLs (Etapa 1)")
    print("  2. 📊 Extraer Estadísticas (Etapa 2)")
    print("  0. ❌ Salir del sistema")
    print("=" * 45)

def main():
    while True:
        mostrar_menu()
        opcion = input("\nSelecciona una opción (0-2): ").strip()

        if opcion == '1':
            print("\n▶ Iniciando Explorador de URLs...")
            run_url_explorer()

        elif opcion == '2':
            print("\n▶ Preparando extracción de estadísticas...")

            # Verificamos si la carpeta existe
            if not os.path.exists(INPUT_FOLDER):
                print("\n❌ La carpeta de datos no existe aún. Ejecuta la Etapa 1 primero.")
                continue

            # Buscamos todos los archivos JSON en la carpeta
            archivos = [f for f in os.listdir(INPUT_FOLDER) if f.endswith('.json')]

            if not archivos:
                print("\n❌ No hay archivos JSON disponibles. Ejecuta la Etapa 1 primero.")
                continue

            # Mostramos el sub-menú dinámico con los archivos
            print("\n📂 Archivos disponibles:")
            for i, archivo in enumerate(archivos, 1):
                print(f"  {i}. {archivo}")

            print("  c. Cancelar y volver al menú principal")

            seleccion = input(f"\nElige el archivo a procesar (1-{len(archivos)}): ").strip().lower()

            if seleccion == 'c':
                continue

            try:
                indice = int(seleccion) - 1
                if 0 <= indice < len(archivos):
                    archivo_elegido = archivos[indice]
                    print(f"\n▶ Ejecutando Etapa 2 para: {archivo_elegido}")
                    procesar_archivo_ronda(archivo_elegido)
                else:
                    print("\n❌ Número fuera de rango. Intenta nuevamente.")
            except ValueError:
                print("\n❌ Entrada inválida. Debes ingresar un número.")

        elif opcion == '0':
            print("\nCerrando Oráculo. ¡Hasta pronto!\n")
            break

        else:
            print("\n❌ Opción no válida. Por favor, selecciona 0, 1 o 2.")

if __name__ == '__main__':
    main()