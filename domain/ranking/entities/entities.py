"""
Entidades competitivas nominales del sistema de ranking.

Estas clases:
- no contienen lógica
- no contienen estado mutable
- existen para tipado fuerte y claridad semántica
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class PlayerEntity:
    player_id: int


@dataclass(frozen=True)
class TeamEntity:
    team_id: int


@dataclass(frozen=True)
class CharacterEntity:
    character_id: int


@dataclass(frozen=True)
class PlayerCharacterEntity:
    player_id: int
    character_id: int
