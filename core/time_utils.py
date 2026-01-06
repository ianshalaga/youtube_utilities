"""
NOTAS DE IMPLEMENTACIÓN (uso personal)

- // (floor division): división entera; devuelve el cociente truncado.
- % (módulo): devuelve el resto de una división.
- f"{value:06.3f}":
    - 06 → ancho total mínimo (incluye dígitos, punto y decimales)
    - .3f → número flotante con 3 decimales fijos
- mkvmerge requiere el formato HH:MM:SS.mmm para --split time/parts.
- YouTube timestamps:
    - Reconocen MM:SS y HH:MM:SS.
    - No reconocen milisegundos.
- Padding consistente:
    - Cuando existen horas, se usa HH:MM:SS.
    - Cuando no existen, se usa MM:SS.
- int(seconds):
    - Trunca los decimales (no redondea).
    - Es suficiente para timestamps de YouTube.
- Las validaciones son preventivas:
    - No deberían dispararse en flujos normales.
"""


def seconds_to_hhmmss_ms(seconds: float) -> str:
    """
    Convierte una duración en segundos a formato HH:MM:SS.mmm.

    Este formato es compatible con herramientas como mkvmerge para
    operaciones de corte basadas en tiempo.

    Args:
        seconds:
            Duración en segundos (puede incluir decimales).

    Returns:
        Cadena con el tiempo formateado como HH:MM:SS.mmm.

    Raises:
        ValueError:
            Si la duración es negativa.
    """
    if seconds < 0:
        raise ValueError("Duration cannot be negative")

    # Cálculo explícito de horas, minutos y segundos para mayor claridad
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60

    return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"


def seconds_to_youtube_timestamp(
    seconds: float,
    *,
    use_hours: bool
) -> str:
    if not isinstance(seconds, (int, float)):
        raise TypeError("seconds must be int or float")

    if seconds < 0:
        raise ValueError("seconds cannot be negative")

    total_seconds = int(seconds)

    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60

    if use_hours:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"

    return f"{minutes:02d}:{secs:02d}"
