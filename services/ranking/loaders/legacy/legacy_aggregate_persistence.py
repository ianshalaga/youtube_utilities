"""
Legacy Aggregate Persistence
============================

Responsabilidad:

- Traducir NormalizedSeasonAggregate a entidades ORM.
- Persistir árbol completo:
    Season → Event → Duel → Battle → Round → Participants
- Operar dentro de una sesión SQLAlchemy.

No:
- Ejecuta agregación.
- Valida dominio.
- Lee CSV.
- Deriva lógica.

Es una capa de infraestructura.
"""

from typing import Tuple
from sqlalchemy.orm import Session

from services.ranking.loaders.legacy.legacy_season_aggregator import NormalizedSeasonAggregate
from services.ranking.loaders.legacy.legacy_event_aggregator import NormalizedEventAggregate
from services.ranking.loaders.legacy.legacy_duel_aggregator import NormalizedDuelAggregate
from services.ranking.loaders.legacy.row_legacy_normalizer import (
    NormalizedParticipant, NormalizedBattleAggregate,
    NormalizedRoundContext
)

from domain.ranking.scoring.scoring_v1 import RoundScoringV1

from services.ranking.storage.models import (
    Season, Event, Duel, Battle, Round,
    Region, Platform, EventType, Franchise,
    Game, GameVersionPlatform, DuelType,
    Country, Player, Team, Stage, RoundResult
)

_COUNTRY_NAME_ISO_CODE_3166_ALPHA_2_MAP = {
    "Argentina": "AR",
    "Chile": "CL",
    "Paraaguay": "PY",
    "Brasil": "BR",
}


class LegacyAggregatePersistence:
    """
    Servicio de persistencia de aggregates legacy.

    Traductor entre modelo normalizado y modelo ORM.
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    # ---------------------------------------------------------

    def persist(
        self,
        seasons: Tuple[NormalizedSeasonAggregate, ...]
    ) -> None:
        """
        Persiste el árbol completo de aggregates.

        Se asume que los aggregates son coherentes.
        """
        # SEASON → EVENT
        for season in seasons:
            season_model = self._persist_season(season)

            # EVENT → DUEL
            for event in season.events:
                region_model = self._persist_region(event)
                event_type_model = self._persist_event_type(event)
                platform_model = self._persist_platform(event)
                game_franchise_model = self._persist_game_franchise(event)
                game_model = self._persist_game(event, game_franchise_model)
                game_version_platform_model = self._persist_game_version_platform(
                    event, game_model, platform_model)

                event_model = self._persist_event(
                    event,
                    season_model,
                    region_model,
                    event_type_model,
                    game_version_platform_model
                )

                # DUEL → BATTLE
                for duel in event.duels:
                    duel_type_model = self._persist_duel_type(duel)
                    team_duel_type_model = self._persist_team_duel_type(duel)
                    players: set[Player] = set()
                    teams: set[Team] = set()
                    for battle in duel.battles:
                        for participant in battle.participants:
                            country_model = self._persist_country(participant)
                            player_model = self._persist_player(
                                participant, country_model)
                            team_model = self._persist_team(participant)

                            players.add(player_model)
                            teams.add(team_model)

                    winner_player_model = None
                    for player in players:
                        if player.nickname == duel.winner_player_name:
                            winner_player_model = player
                            break

                    winner_team_model = None
                    for team in teams:
                        if team.name == duel.winner_team_name:
                            winner_team_model = team
                            break

                    duel_model = self._persist_duel(
                        duel,
                        event_model,
                        duel_type_model,
                        team_duel_type_model,
                        winner_player_model,
                        winner_team_model
                    )

                    # BATTLE → ROUND
                    for battle in duel.battles:
                        stage_model = self._persist_stage(
                            battle, game_version_platform_model)

                        winner_model = None
                        loser_model = None

                        if not battle.battle.is_draw:
                            winner_player = None
                            loser_player = None

                            if battle.battle.winner_position == 1:
                                winner_player = battle.participants[0]
                                loser_player = battle.participants[1]
                            elif battle.battle.winner_position == 2:
                                winner_player = battle.participants[1]
                                loser_player = battle.participants[0]

                            if winner_player is None or loser_player is None:
                                raise ValueError(
                                    "Battle is no a draw, must have a winner and a loser."
                                )

                            winner_country_model = self._persist_country(
                                winner_player)
                            loser_country_model = self._persist_country(
                                loser_player)

                            winner_model = self._persist_player(
                                winner_player, winner_country_model
                            )
                            loser_model = self._persist_player(
                                loser_player, loser_country_model
                            )

                        battle_model = self._persist_battle(
                            battle,
                            duel_model,
                            stage_model,
                            winner_model,
                            loser_model
                        )

                        # ROUND
                        for round in battle.rounds:
                            p1_result = round.p1_result_code
                            p2_result = round.p2_result_code

                            is_draw = False
                            if p1_result == p2_result and RoundScoringV1.is_draw(p1_result):
                                is_draw = True
                                winner_model = None
                                loser_model = None

                            player1_model = None
                            player2_model = None

                            if RoundScoringV1.is_win(p1_result) or RoundScoringV1.is_perfect_win(p1_result):
                                winner_country_model = self._persist_country(
                                    battle.participants[0])
                                winner_model = self._persist_player(
                                    battle.participants[0], winner_country_model
                                )
                                loser_country_model = self._persist_country(
                                    battle.participants[1])
                                loser_model = self._persist_player(
                                    battle.participants[1], loser_country_model
                                )
                                player1_model = winner_model
                                player2_model = loser_model
                            elif RoundScoringV1.is_win(p2_result) or RoundScoringV1.is_perfect_win(p2_result):
                                winner_country_model = self._persist_country(
                                    battle.participants[1])
                                winner_model = self._persist_player(
                                    battle.participants[1], winner_country_model
                                )
                                loser_country_model = self._persist_country(
                                    battle.participants[0])
                                loser_model = self._persist_player(
                                    battle.participants[0], loser_country_model
                                )
                                player1_model = loser_model
                                player2_model = winner_model

                            round_model = self._persist_round(
                                round,
                                battle_model,
                                winner_model,
                                loser_model,
                                is_draw
                            )

                            self._persist_round_result(
                                p1_result,
                                round_model,
                                player1_model
                            )

                            self._persist_round_result(
                                p2_result,
                                round_model,
                                player2_model
                            )

        self._session.flush()

    # ---------------------------------------------------------
    # Private persistence helpers
    # ---------------------------------------------------------

    def _get_or_create(
        self,
        model: type, defaults=dict[str: any] | None,
        **kwargs
    ) -> object:
        """
        Patrón genérico get_or_create.

        - Busca por kwargs.
        - Si no existe, crea con kwargs + defaults.
        """

        instance = (
            self._session.query(model)
            .filter_by(**kwargs)
            .one_or_none()
        )

        if instance:
            return instance

        params = dict(kwargs)
        if defaults:
            params.update(defaults)

        instance = model(**params)
        self._session.add(instance)
        self._session.flush()  # asegura PK disponible

        return instance

    # SEASON persistence
    def _persist_season(self, season: NormalizedSeasonAggregate):
        return self._get_or_create(
            Season,
            name=season.season_name,
            defaults={
                "start_date": season.start_date,
                "end_date": season.end_date,
            }
        )

    # EVENT persistence
    def _persist_region(self, event: NormalizedEventAggregate):
        return self._get_or_create(
            Region,
            name=event.region_name
        )

    def _persist_event_type(self, event: NormalizedEventAggregate):
        return self._get_or_create(
            EventType,
            name=event.event_type_name
        )

    def _persist_platform(self, event: NormalizedEventAggregate):
        return self._get_or_create(
            Platform,
            name=event.platform_name
        )

    def _persist_game_franchise(self, event: NormalizedEventAggregate):
        return self._get_or_create(
            Franchise,
            name=event.game_franchise_name
        )

    def _persist_game(self, event: NormalizedEventAggregate, game_franchise_model: Franchise):
        return self._get_or_create(
            Game,
            name=event.game_name,
            franchise_id=game_franchise_model.id
        )

    def _persist_game_version_platform(
        self,
        event: NormalizedEventAggregate,
        game_model: Game,
        platform_model: Platform
    ):
        return self._get_or_create(
            GameVersionPlatform,
            game_id=game_model.id,
            platform_id=platform_model.id,
            version=event.game_version
        )

    def _persist_event(
        self,
        event: NormalizedEventAggregate,
        season_model: Season,
        region_model: Region,
        event_type_model: EventType,
        game_version_platform_model: GameVersionPlatform
    ):
        return self._get_or_create(
            Event,
            season_id=season_model.id,
            sequence_number=event.sequence_number,
            defaults={
                "name": event.event.event_name,
                "event_date": event.event.event_date,
                "region_id": region_model.id,
                "event_type_id": event_type_model.id,
                "game_version_platform_id": game_version_platform_model.id,
                "brackets_url": event.event.brackets_url,
                "playlist_url": event.event.playlist_url,
            }
        )

    # DUEL persistence
    def _persist_duel_type(self, duel: NormalizedDuelAggregate):
        return self._get_or_create(
            DuelType,
            name=duel.duel.normal_duel_type_name
        )

    def _persist_team_duel_type(self, duel: NormalizedDuelAggregate):
        return self._get_or_create(
            DuelType,
            name=duel.duel.team_duel_type_name
        )

    def _persist_country(self, participant: NormalizedParticipant):
        return self._get_or_create(
            Country,
            name=participant.country,
            iso_code=_COUNTRY_NAME_ISO_CODE_3166_ALPHA_2_MAP[participant.country]
        )

    def _persist_player(self, participant: NormalizedParticipant, country_model: Country):
        return self._get_or_create(
            Player,
            nickname=participant.player_name,
            country_id=country_model.id
        )

    def _persist_team(self, participant: NormalizedParticipant):
        return self._get_or_create(
            Team,
            name=participant.team_name
        )

    def _persist_duel(
        self,
        duel: NormalizedDuelAggregate,
        event_model: Event,
        duel_type_model: DuelType,
        team_duel_type_model: DuelType,
        winner_player_model: Player,
        winner_team_model: Team
    ):
        return self._get_or_create(
            Duel,
            event_id=event_model.id,
            sequence_number=duel.duel.normal_duel_sequence_number,
            defaults={
                "duel_type_id": duel_type_model.id,
                "team_duel_type_id": team_duel_type_model.id,
                "is_team_duel": duel.duel.is_team_duel,
                "team_duel_sequence_number": duel.duel.team_duel_sequence_number,
                "video_url": duel.duel.duel_video_url,
                "winner_id": winner_player_model.id,
                "winner_team_id": winner_team_model.id,
            }
        )

    # BATTLE persistence
    def _persist_stage(self, battle, game_version_platform_model):
        return (
            self._get_or_create(
                Stage,
                name=battle.stage_name,
                game_version_platform_id=game_version_platform_model.id
            )
        )

    def _persist_battle(
            self,
            battle: NormalizedBattleAggregate,
            duel_model: Duel,
            stage_model: Stage,
            winner_model: Player,
            loser_model: Player
    ):
        return (
            self._get_or_create(
                Battle,
                duel_id=duel_model.id,
                stage_id=stage_model.id,
                winner_id=winner_model.id,
                loser_id=loser_model.id,
                sequence_number=battle.battle.battle_sequence_number,
                is_draw=battle.battle.is_draw
            )
        )

    # ROUND persistence
    def _persist_round(
        self,
        round: NormalizedRoundContext,
        battle_model: Battle,
        winner_model: Player,
        loser_model: Player,
        is_draw: bool
    ):
        return self._get_or_create(
            Round,
            battle_id=battle_model.id,
            winner_id=winner_model.id,
            loser_id=loser_model.id,
            is_draw=is_draw,
            sequence_number=round.round_sequence_number,
        )

    def _persist_round_result(
        self,
        result_code: str,
        round_model: Round,
        player_model: Player,
    ):
        return self._get_or_create(
            RoundResult,
            round_id=round_model.id,
            player_id=player_model.id,
            result_code=result_code
        )
