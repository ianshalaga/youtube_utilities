"""
Filtros declarativos para consultas de ranking.

Este módulo define la estructura semántica utilizada para describir
un universo competitivo sobre el cual se calculan rankings.

Reglas:
- NO contiene lógica de base de datos
- NO importa ORM
- NO usa SQLAlchemy
- Objetos puros, inmutables y declarativos
"""

from dataclasses import dataclass
from typing import Optional


# ─────────────────────────────────────────────────────────────
# Objeto raíz de consulta de ranking
# ─────────────────────────────────────────────────────────────

@dataclass(frozen=True, slots=True)
class RankingQuery:
    """
    Objeto raíz que describe una consulta completa de ranking.

    Este es el ÚNICO objeto que debe viajar entre:
        app → provider → repository
    """

    scope: RankingScopeFilter

    duel: Optional[DuelFilter] = None
    participant: Optional[ParticipantFilter] = None
    battle: Optional[BattleContextFilter] = None
    player_meta: Optional[PlayerMetaFilter] = None

    def validate(self) -> None:
        """
        Validación semántica opcional.
        Llamar explícitamente si se desea validar la coherencia del query.
        """

        if self.participant and not self.duel:
            raise ValueError(
                "ParticipantFilter requiere que DuelFilter esté definido."
            )

        if self.battle and not self.duel:
            raise ValueError(
                "BattleContextFilter requiere que DuelFilter esté definido."
            )

# ─────────────────────────────────────────────────────────────
# Scope / Contexto competitivo
# ─────────────────────────────────────────────────────────────


@dataclass(frozen=True, slots=True)
class RankingScopeFilter:
    """
    Define DÓNDE ocurre la competencia.
    Es el contexto competitivo de más alto nivel.
    """

    # Season / Event
    season_id: Optional[int] = None
    event_id: Optional[int] = None
    event_type_id: Optional[int] = None
    region_id: Optional[int] = None

    # Contexto del juego
    game_id: Optional[int] = None
    game_version: Optional[str] = None
    platform_id: Optional[int] = None

    # Franquicia
    franchise_id: Optional[int] = None


# ─────────────────────────────────────────────────────────────
# Contexto de duelo
# ─────────────────────────────────────────────────────────────

@dataclass(frozen=True, slots=True)
class DuelFilter:
    """
    Define QUÉ tipo de duelo se considera.
    """

    duel_id: Optional[int] = None
    duel_type_id: Optional[int] = None   # FT2, FT3, etc.


# ─────────────────────────────────────────────────────────────
# Contexto de participación
# ─────────────────────────────────────────────────────────────

@dataclass(frozen=True, slots=True)
class ParticipantFilter:
    """
    Define QUIÉN participa y EN QUÉ ROL.
    """

    player_id: Optional[int] = None
    player_position: Optional[int] = None   # P1 / P2
    team_id: Optional[int] = None


# ─────────────────────────────────────────────────────────────
# Contexto de battle / personaje
# ─────────────────────────────────────────────────────────────

@dataclass(frozen=True, slots=True)
class BattleContextFilter:
    """
    Define el entorno de la battle y el contexto del personaje.
    """

    stage_id: Optional[int] = None
    game_character_id: Optional[int] = None
    character_identity_id: Optional[int] = None


# ─────────────────────────────────────────────────────────────
# Metadata del jugador (atributos no competitivos)
# ─────────────────────────────────────────────────────────────

@dataclass(frozen=True, slots=True)
class PlayerMetaFilter:
    """
    Define atributos externos del jugador que no forman parte
    directa de la mecánica competitiva.
    """

    country_id: Optional[int] = None
