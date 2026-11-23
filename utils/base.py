import logging
import random
import time


def random_sleep(min_s, max_s):
    """Genera un tiempo de espera aleatorio para evitar bloqueos."""
    delay = random.uniform(min_s, max_s)
    logging.info("Esperando %.2f segundos antes de continuar...", delay)
    time.sleep(delay)
