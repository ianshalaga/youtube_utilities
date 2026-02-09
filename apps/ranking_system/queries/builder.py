# Filtros DB
from services.ranking.filters import (
    RankingQuery, RankingScopeFilter, DuelFilter,
    ParticipantFilter, BattleContextFilter, PlayerMetaFilter
)
# Filtros humanos
from services.ranking.config.filters import RankingFilters
from services.ranking.storage.models import (
    Season, Event, EventType, Region, Game, Platform,
    Franchise, DuelType, Player, Team, Stage, CharacterIdentity,
    Country
)

from apps.ranking_system.resolvers.common import resolve_id_by_name


class RankingQueryBuilder:
    def __init__(self, session):
        self._session = session

    def build(self, filters: RankingFilters) -> RankingQuery:
        return RankingQuery(
            scope=self._build_scope(filters),
            duel=self._build_duel(filters),
            participant=self._build_participant(filters),
            battle=self._build_battle(filters),
            player_meta=self._build_player(filters),
        )

    def _build_scope(self, filters: RankingFilters) -> RankingScopeFilter:
        scope = filters.scope

        return RankingScopeFilter(
            # Season / Event Context
            season_id=resolve_id_by_name(
                session=self._session,
                model=Season,
                name=scope.season_name,
                label="season",
            ),
            event_id=resolve_id_by_name(
                session=self._session,
                model=Event,
                name=scope.event_name,
                label="event",
            ),
            event_type_id=resolve_id_by_name(
                session=self._session,
                model=EventType,
                name=scope.event_type_name,
                label="event_type",
            ),
            region_id=resolve_id_by_name(
                session=self._session,
                model=Region,
                name=scope.region_name,
                label="region",
            ),
            # Game Context
            game_id=resolve_id_by_name(
                session=self._session,
                model=Game,
                name=scope.game_name,
                label="game",
            ),
            platform_id=resolve_id_by_name(
                session=self._session,
                model=Platform,
                name=scope.event_platform,
                label="platform",
            ),
            game_version=scope.game_version,
            # Franchise
            franchise_id=resolve_id_by_name(
                session=self._session,
                model=Franchise,
                name=scope.game_franchise_name,
                label="franchise",
            ),
        )

    def _build_duel(self, filters: RankingFilters) -> DuelFilter:
        duel = filters.duel

        return DuelFilter(
            duel_id=filters.duel.duel_id,
            duel_type_id=resolve_id_by_name(
                session=self._session,
                model=DuelType,
                name=duel.duel_type_name,
                label="duel_type",
            )
        )

    def _build_participant(self, filters: RankingFilters) -> ParticipantFilter:
        participant = filters.participant

        return ParticipantFilter(
            player_id=resolve_id_by_name(
                session=self._session,
                model=Player,
                name=participant.player_name,
                label="player",
            ),
            team_id=resolve_id_by_name(
                session=self._session,
                model=Team,
                name=participant.team_name,
                label="team",
            ),
        )

    def _build_battle(self, filters: RankingFilters) -> BattleContextFilter:
        battle = filters.battle

        return BattleContextFilter(
            player_position=battle.participant_position,
            stage_id=resolve_id_by_name(
                session=self._session,
                model=Stage,
                name=battle.stage_name,
                label="stage",
            ),
            character_identity_id=resolve_id_by_name(
                session=self._session,
                model=CharacterIdentity,
                name=battle.character_identity_name,
                label="character_identity",
            )
        )

    def _build_player(self, filters: RankingFilters) -> PlayerMetaFilter:
        player = filters.player

        return PlayerMetaFilter(
            country_id=resolve_id_by_name(
                session=self._session,
                model=Country,
                name=None,
                extra_filters={"iso_code": player.country_iso_code},
                label="country",
            ),
        )
