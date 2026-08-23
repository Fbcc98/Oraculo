"""Funciones de normalizacion compartidas por los procesadores ETL."""

from datetime import datetime, timezone


class Common:
    """Conversiones seguras que preservan valores ausentes como ``None``."""

    @staticmethod
    def entero(valor):
        if valor is None or isinstance(valor, bool):
            return None
        try:
            return int(float(str(valor).strip()))
        except (TypeError, ValueError):
            return None

    @staticmethod
    def decimal(valor):
        if valor is None or isinstance(valor, bool):
            return None
        try:
            texto = str(valor).strip().replace("km", "").strip()
            return float(texto)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def porcentaje(valor):
        """Convierte ``55%`` en ``0.55``; conserva proporciones ya normalizadas."""
        if valor is None or isinstance(valor, bool):
            return None
        try:
            texto = str(valor).strip()
            if texto.endswith("%"):
                return float(texto[:-1].strip()) / 100.0
            numero = float(texto)
            return numero / 100.0 if numero > 1 else numero
        except (TypeError, ValueError):
            return None

    @staticmethod
    def booleano(valor):
        if valor is None:
            return None
        if isinstance(valor, bool):
            return valor
        if isinstance(valor, (int, float)):
            return bool(valor)
        texto = str(valor).strip().lower()
        if texto in {"true", "1", "si", "sí", "yes"}:
            return True
        if texto in {"false", "0", "no"}:
            return False
        return None

    @staticmethod
    def fecha_desde_timestamp(valor):
        timestamp = Common.entero(valor)
        if timestamp is None:
            return None
        try:
            return datetime.fromtimestamp(timestamp, tz=timezone.utc).date().isoformat()
        except (OverflowError, OSError, ValueError):
            return None

