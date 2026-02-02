"""
Repositorio de datos para el sistema de ranking.

Responsabilidades:
- Construir queries SQLAlchemy completas
- Traducir RankingQuery (semántico) a SQL
- Extraer datos crudos de competencia
- NO contiene lógica de cálculo de ranking
"""

from typing import Iterable

from sqlalchemy import and_
from sqlalchemy.orm import Session, Query

from services.ranking.filters import (
    RankingQuery,
    RankingScopeFilter,
    DuelFilter,
    ParticipantFilter,
    BattleContextFilter,
    PlayerMetaFilter,
)

from services.ranking.storage.models import (
    RoundResult,
    Round,
    Battle,
    BattleParticipant,
    Duel,
    DuelType,
    DuelTeam,
    Team,
    Event,
    EventType,
    Season,
    Region,
    Stage,
    GameCharacter,
    CharacterIdentity,
    GameVersionPlatform,
    Game,
    Platform,
    Franchise,
    Player,
    Country,
)


class RankingRepository:
    """
    Repositorio encargado de extraer datos competitivos
    desde la base de datos para el sistema de ranking.
    """

    # ─────────────────────────────────────────────────────────
    # API pública del repository
    # ─────────────────────────────────────────────────────────

    def fetch_round_results(
        self,
        session: Session,
        ranking_query: RankingQuery,
    ) -> Iterable[RoundResult]:
        """
        Ejecuta una consulta completa de ranking y devuelve
        los RoundResult que cumplen con los filtros indicados.
        """

        ranking_query.validate()

        query = self._build_base_query(session)

        query = self._apply_scope_filters(query, ranking_query.scope)

        if ranking_query.duel:
            query = self._apply_duel_filters(query, ranking_query.duel)

        if ranking_query.participant:
            query = self._apply_participant_filters(
                query, ranking_query.participant
            )

        if ranking_query.battle:
            query = self._apply_battle_context_filters(
                query, ranking_query.battle
            )

        if ranking_query.player_meta:
            query = self._apply_player_meta_filters(
                query, ranking_query.player_meta
            )

        return query.all()

    # ─────────────────────────────────────────────────────────
    # Query base
    # ─────────────────────────────────────────────────────────

    def _build_base_query(self, session: Session) -> Query:
        """
        Construye la query base completamente unida, partiendo
        desde RoundResult, que es el evento competitivo atómico.

        Esta query NO aplica filtros.
        """

        query = session.query(RoundResult)

        query = query.join(Round, Round.id == RoundResult.round_id)
        query = query.join(Battle, Battle.id == Round.battle_id)
        query = query.join(Duel, Duel.id == Battle.duel_id)
        query = query.join(Event, Event.id == Duel.event_id)
        query = query.outerjoin(Season, Season.id == Event.season_id)

        query = query.join(DuelType, DuelType.id == Duel.duel_type_id)
        query = query.join(Stage, Stage.id == Battle.stage_id)

        query = query.join(
            GameVersionPlatform,
            GameVersionPlatform.id == Stage.game_version_platform_id,
        )
        query = query.join(Game, Game.id == GameVersionPlatform.game_id)
        query = query.join(Platform, Platform.id ==
                           GameVersionPlatform.platform_id)
        query = query.join(Franchise, Franchise.id == Game.franchise_id)

        query = query.join(EventType, EventType.id == Event.event_type_id)
        query = query.join(Region, Region.id == Event.region_id)

        query = query.join(Player, Player.id == RoundResult.player_id)
        query = query.outerjoin(Country, Country.id == Player.country_id)

        query = query.join(
            BattleParticipant,
            and_(
                BattleParticipant.battle_id == Battle.id,
                BattleParticipant.player_id == Player.id,
            ),
        )

        query = query.join(
            GameCharacter,
            GameCharacter.id == BattleParticipant.game_character_id,
        )
        query = query.join(
            CharacterIdentity,
            CharacterIdentity.id == GameCharacter.character_identity_id,
        )

        query = query.outerjoin(
            DuelTeam,
            DuelTeam.id == BattleParticipant.duel_team_id,
        )
        query = query.outerjoin(
            Team,
            Team.id == DuelTeam.team_id,
        )

        return query

    # ─────────────────────────────────────────────────────────
    # Aplicación de filtros
    # ─────────────────────────────────────────────────────────

    def _apply_scope_filters(
        self,
        query: Query,
        scope: RankingScopeFilter,
    ) -> Query:
        """Aplica filtros de contexto competitivo (scope)."""

        if scope.season_id is not None:
            query = query.filter(Season.id == scope.season_id)

        if scope.event_id is not None:
            query = query.filter(Event.id == scope.event_id)

        if scope.event_type_id is not None:
            query = query.filter(EventType.id == scope.event_type_id)

        if scope.region_id is not None:
            query = query.filter(Region.id == scope.region_id)

        if scope.game_id is not None:
            query = query.filter(Game.id == scope.game_id)

        if scope.game_version is not None:
            query = query.filter(
                GameVersionPlatform.version == scope.game_version
            )

        if scope.platform_id is not None:
            query = query.filter(Platform.id == scope.platform_id)

        if scope.franchise_id is not None:
            query = query.filter(Franchise.id == scope.franchise_id)

        return query

    def _apply_duel_filters(
        self,
        query: Query,
        duel: DuelFilter,
    ) -> Query:
        """Aplica filtros relacionados al duelo."""

        if duel.duel_id is not None:
            query = query.filter(Duel.id == duel.duel_id)

        if duel.duel_type_id is not None:
            query = query.filter(DuelType.id == duel.duel_type_id)

        return query

    def _apply_participant_filters(
        self,
        query: Query,
        participant: ParticipantFilter,
    ) -> Query:
        """Aplica filtros relacionados a la participación del jugador."""

        if participant.player_id is not None:
            query = query.filter(Player.id == participant.player_id)

        if participant.player_position is not None:
            query = query.filter(
                BattleParticipant.position == participant.player_position
            )

        if participant.team_id is not None:
            query = query.filter(Team.id == participant.team_id)

        return query

    def _apply_battle_context_filters(
        self,
        query: Query,
        battle: BattleContextFilter,
    ) -> Query:
        """Aplica filtros de entorno de battle y personaje."""

        if battle.stage_id is not None:
            query = query.filter(Stage.id == battle.stage_id)

        if battle.game_character_id is not None:
            query = query.filter(GameCharacter.id == battle.game_character_id)

        if battle.character_identity_id is not None:
            query = query.filter(
                CharacterIdentity.id == battle.character_identity_id
            )

        return query

    def _apply_player_meta_filters(
        self,
        query: Query,
        meta: PlayerMetaFilter,
    ) -> Query:
        """Aplica filtros de metadata del jugador."""

        if meta.country_id is not None:
            query = query.filter(Country.id == meta.country_id)

        return query
