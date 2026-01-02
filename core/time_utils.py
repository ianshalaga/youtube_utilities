def seconds_to_hhmmss_ms(seconds: float) -> str:
    if seconds < 0:
        raise ValueError("Duration cannot be negative")

    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60

    return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"
