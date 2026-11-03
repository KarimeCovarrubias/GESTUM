"""
Hora y fecha oficiales de GESTUM: siempre UTC-7 (Culiacán / Mazatlán),
sin importar en qué zona horaria esté configurada la computadora o el
servidor donde corra la app. Así los registros de la BD y la racha usan
el mismo reloj.

"""

from datetime import datetime, timedelta, timezone

ZONA = timezone(timedelta(hours=-7))


def ahora():
    return datetime.now(ZONA)


def hoy():
    """Fecha de hoy (00:00 a 23:59 en UTC-7)."""
    return ahora().date()


def ahora_texto():
    """Fecha y hora como texto para guardar en SQLite: 2026-11-03 16:16:05"""
    return ahora().strftime("%Y-%m-%d %H:%M:%S")