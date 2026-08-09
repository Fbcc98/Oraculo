import random
import time

def random_sleep(min_s, max_s):
    """Genera un tiempo de espera aleatorio para evitar bloqueos."""
    delay = random.uniform(min_s, max_s)
    print(f"   [⏳] Esperando {delay:.2f} segundos para simular comportamiento humano...")
    time.sleep(delay)