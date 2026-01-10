"""
NOTAS DE IMPLEMENTACIÓN (uso personal)

- Se determina primero la cantidad de partes (K).
- K se calcula a partir de la duración total y el target.
- Luego se equilibran las partes alrededor de una duración ideal.
- No se reordenan ni cortan videos.
- Se evita crear una última parte residual.
- abs(): valor absoluto.
"""

from pathlib import Path
from typing import List

from services.media.media_provider import MediaProvider


class VideoPartitioner:
    """
    Divide una lista ordenada de videos en partes contiguas
    equilibradas en duración.
    """

    def __init__(self, _media_provider: MediaProvider):
        self._media_provider = _media_provider

    def partition(
        self,
        videos: List[Path],
        target_duration: float
    ) -> List[List[Path]]:

        if not videos:
            return []

        if target_duration <= 0:
            raise ValueError("target_duration must be > 0")

        durations = [self._media_provider.duration(v) for v in videos]
        total_duration = sum(durations)

        # Número de partes deseadas
        parts_count = max(1, round(total_duration / target_duration))
        ideal_duration = total_duration / parts_count

        partitions: List[List[Path]] = []

        current_part: List[Path] = []
        current_duration = 0.0
        remaining_parts = parts_count

        for video, video_duration in zip(videos, durations):

            # Siempre debemos dejar al menos una parte para cada parte restante
            if current_part:
                candidate_duration = current_duration + video_duration

                diff_with = abs(candidate_duration - ideal_duration)
                diff_without = abs(current_duration - ideal_duration)

                # Cierra la parte si empeora el balance
                if diff_with > diff_without and remaining_parts > 1:
                    partitions.append(current_part)
                    current_part = []
                    current_duration = 0.0
                    remaining_parts -= 1

            current_part.append(video)
            current_duration += video_duration

        if current_part:
            partitions.append(current_part)

        # ───────────────────────────────
        # Corrección CRÍTICA:
        # evita una última parte residual
        # ───────────────────────────────
        if len(partitions) >= 2:
            last_duration = sum(
                self._media_provider.duration(v) for v in partitions[-1]
            )

            if last_duration < ideal_duration * 0.5:
                partitions[-2].extend(partitions[-1])
                partitions.pop()

        return partitions
