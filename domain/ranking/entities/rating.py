"""
Rating representa el valor comparable del ranking.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Rating:
    value: float
