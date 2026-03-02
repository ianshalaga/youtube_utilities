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
from collections import defaultdict

from sqlalchemy.orm import Session

from services.ranking.loaders.legacy.legacy_season_aggregator import NormalizedSeasonAggregate
from services.ranking.loaders.legacy.legacy_event_aggregator import NormalizedEventAggregate
from services.ranking.loaders.legacy.legacy_duel_aggregator import NormalizedDuelAggregate
from services.ranking.loaders.legacy.row_legacy_normalizer import (
    NormalizedParticipant, NormalizedBattleAggregate,
    NormalizedRoundContext
)

from services.ranking.storage.models import (
    Season, Event, Duel, Battle, Round,
    Region, Platform, EventType, Franchise,
    Game, GameVersionPlatform, DuelType,
    Country, Player, Team, Stage, RoundResult,
    CharacterIdentity, GameCharacter, PlayerAlias,
    DuelParticipant, DuelTeam, DuelTeamMember,
    BattleParticipant
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
        self._cache = {}

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

                game_model = self._persist_game(
                    event=event,
                    game_franchise_model=game_franchise_model
                )

                game_version_platform_model = self._persist_game_version_platform(
                    event=event,
                    game_model=game_model,
                    platform_model=platform_model
                )

                event_model = self._persist_event(
                    event=event,
                    season_model=season_model,
                    region_model=region_model,
                    event_type_model=event_type_model,
                    game_version_platform_model=game_version_platform_model
                )
                # @@@@
                # DUEL → BATTLE
                for duel in event.duels:
                    duel_type_model = self._persist_duel_type(duel)

                    team_duel_type_model = None
                    if duel.duel.is_team_duel:
                        team_duel_type_model = self._persist_team_duel_type(
                            duel)

                    players: set[Player] = set()
                    teams: set[Team] = set()
                    players_by_team: defaultdict[Team,
                                                 set[Player]] = defaultdict(set)
                    for battle in duel.battles:
                        for participant in battle.participants:
                            country_model = self._persist_country(participant)
                            player_model = self._persist_player(
                                participant, country_model)

                            # @@@@ TODO: Revisar si se necesita la asignación
                            player_alias_model = self._persist_player_alias(
                                participant, player_model)

                            character_identity_model = self._persist_character_identity(
                                participant,
                                game_franchise_model
                            )

                            # @@@@ TODO: Revisar si se necesita la asignación
                            game_character_model = self._persist_game_character(
                                character_identity_model,
                                game_version_platform_model
                            )

                            players.add(player_model)

                            if duel.duel.is_team_duel:
                                team_model = self._persist_team(participant)
                                teams.add(team_model)
                                players_by_team[team_model].add(player_model)

                    winner_player_model = None
                    for player in players:
                        if player.nickname == duel.winner_player_name:
                            winner_player_model = player
                            break

                    if winner_player_model is None:
                        raise ValueError(
                            f"Winner player not found: {duel.winner_player_name}")

                    winner_team_model = None
                    if duel.duel.is_team_duel:
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

                    for player in players:
                        # @@@@ TODO: Revisar si se necesita la asignación
                        duel_participant_model = self._persist_duel_participant(
                            duel_model,
                            player_model
                        )

                    if duel.duel.is_team_duel and len(teams) > 0:
                        for team in teams:
                            duel_team_model = self._persist_duel_team(
                                duel_model,
                                team
                            )

                            for player in players_by_team[team]:
                                # @@@@ TODO: Revisar si se necesita la asignación
                                duel_team_member_model = self._persist_duel_team_member(
                                    duel_team_model,
                                    player_model
                                )

                    # BATTLE → ROUND
                    for battle in duel.battles:
                        stage_model = self._persist_stage(
                            battle, game_version_platform_model)

                        participant_1 = battle.participants[0]
                        participant_2 = battle.participants[1]

                        country_model_1 = self._persist_country(participant_1)
                        country_model_2 = self._persist_country(participant_2)

                        player_1_model = self._persist_player(
                            participant_1, country_model_1)
                        player_2_model = self._persist_player(
                            participant_2, country_model_2)

                        character_identity_1_model = self._persist_character_identity(
                            participant_1,
                            game_franchise_model
                        )
                        character_identity_2_model = self._persist_character_identity(
                            participant_2,
                            game_franchise_model
                        )

                        game_character_1_model = self._persist_game_character(
                            character_identity_1_model,
                            game_version_platform_model
                        )
                        game_character_2_model = self._persist_game_character(
                            character_identity_2_model,
                            game_version_platform_model
                        )

                        if battle.battle.is_draw:
                            winner_model = None
                            loser_model = None
                        elif participant_1.player_name == battle.battle.winner_player_name:
                            winner_model = player_1_model
                            loser_model = player_2_model
                        elif participant_2.player_name == battle.battle.winner_player_name:
                            winner_model = player_2_model
                            loser_model = player_1_model

                        battle_model = self._persist_battle(
                            battle,
                            duel_model,
                            stage_model,
                            winner_model,
                            loser_model
                        )

                        duel_team_1_model = None
                        duel_team_2_model = None
                        if duel.duel.is_team_duel:
                            team_1_model = self._persist_team(participant_1)
                            team_2_model = self._persist_team(participant_2)
                            duel_team_1_model = self._persist_duel_team(
                                duel_model,
                                team_1_model
                            )
                            duel_team_2_model = self._persist_duel_team(
                                duel_model,
                                team_2_model
                            )

                        # @@@@ TODO: Revisar si se necesita la asignación
                        battle_participant_1_model = self._persist_battle_participant(
                            position=1,
                            battle_model=battle_model,
                            player_model=player_1_model,
                            game_character_model=game_character_1_model,
                            duel_tema_model=duel_team_1_model
                        )

                        # @@@@ TODO: Revisar si se necesita la asignación
                        battle_participant_2_model = self._persist_battle_participant(
                            position=2,
                            battle_model=battle_model,
                            player_model=player_2_model,
                            game_character_model=game_character_2_model,
                            duel_tema_model=duel_team_2_model
                        )

                        # ROUND
                        for round in battle.rounds:
                            if round.is_draw:
                                winner_model = None
                                loser_model = None
                            elif round.winner_position == 1:
                                winner_model = player_1_model
                                loser_model = player_2_model
                            elif round.winner_position == 2:
                                winner_model = player_2_model
                                loser_model = player_1_model

                            round_model = self._persist_round(
                                round=round,
                                battle_model=battle_model,
                                winner_model=winner_model,
                                loser_model=loser_model
                            )

                            # @@@@ TODO: Revisar si se necesita la asignación
                            round_result_1_model = self._persist_round_result(
                                round.p1_result_code,
                                round_model,
                                player_1_model
                            )

                            # @@@@ TODO: Revisar si se necesita la asignación
                            round_result_2_model = self._persist_round_result(
                                round.p2_result_code,
                                round_model,
                                player_2_model
                            )

        self._session.flush()

    # ---------------------------------------------------------
    # Private persistence helpers
    # ---------------------------------------------------------

    def _get_or_create(
        self,
        model: type,
        defaults: dict[str: any] | None,
        **kwargs
    ) -> object:
        """
        Patrón genérico get_or_create.

        - Busca por kwargs.
        - Si no existe, crea con kwargs + defaults.
        """
        key = (model, frozenset(kwargs.items()))

        if key in self._cache:
            return self._cache[key]

        instance = (
            self._session.query(model)
            .filter_by(**kwargs)
            .one_or_none()
        )

        if instance:
            self._cache[key] = instance
            return instance

        params = dict(kwargs)
        if defaults:
            params.update(defaults)

        instance = model(**params)
        self._session.add(instance)
        self._session.flush()  # asegura PK disponible

        self._cache[key] = instance

        return instance

    # SEASON persistence
    def _persist_season(
        self,
        season: NormalizedSeasonAggregate
    ):
        return self._get_or_create(
            Season,
            name=season.season_name,
            defaults={
                "start_date": season.start_date,
                "end_date": season.end_date,
            }
        )

    # EVENT persistence
    def _persist_region(
        self: LegacyAggregatePersistence,
        event: NormalizedEventAggregate
    ):
        return self._get_or_create(
            Region,
            name=event.region_name
        )

    def _persist_event_type(
        self: LegacyAggregatePersistence,
        event: NormalizedEventAggregate
    ):
        return self._get_or_create(
            EventType,
            name=event.event_type_name
        )

    def _persist_platform(
        self: LegacyAggregatePersistence,
        event: NormalizedEventAggregate
    ):
        return self._get_or_create(
            Platform,
            name=event.platform_name
        )

    def _persist_game_franchise(
        self: LegacyAggregatePersistence,
        event: NormalizedEventAggregate
    ):
        return self._get_or_create(
            Franchise,
            name=event.game_franchise_name
        )

    def _persist_game(
        self: LegacyAggregatePersistence,
        event: NormalizedEventAggregate,
        game_franchise_model: Franchise
    ):
        return self._get_or_create(
            Game,
            name=event.game_name,
            franchise_id=game_franchise_model.id
        )

    def _persist_game_version_platform(
        self: LegacyAggregatePersistence,
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
        self: LegacyAggregatePersistence,
        event: NormalizedEventAggregate,
        season_model: Season,
        region_model: Region,
        event_type_model: EventType,
        game_version_platform_model: GameVersionPlatform
    ):
        return self._get_or_create(
            Event,
            season_id=season_model.id,
            sequence_number=event.event_sequence_number,
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

    def _persist_player(
        self: LegacyAggregatePersistence,
        participant: NormalizedParticipant,
        country_model: Country
    ):
        return self._get_or_create(
            Player,
            country_id=country_model.id,
            nickname=participant.player_name.upper()
        )

    def _persist_player_alias(
        self: LegacyAggregatePersistence,
        participant: NormalizedParticipant,
        player_model: Player
    ):
        return self._get_or_create(
            PlayerAlias,
            player_id=player_model.id,
            alias=participant.player_name
        )

    def _persist_team(self: LegacyAggregatePersistence, participant: NormalizedParticipant):
        return self._get_or_create(
            Team,
            name=participant.team_name
        )

    def _persist_character_identity(
        self: LegacyAggregatePersistence,
        participant: NormalizedParticipant,
        game_franchise_model: Franchise
    ):
        return self._get_or_create(
            CharacterIdentity,
            franchise_id=game_franchise_model.id,
            name=participant.character_name
        )

    def _persist_game_character(
        self: LegacyAggregatePersistence,
        character_identity_model: CharacterIdentity,
        game_version_platform_model: GameVersionPlatform
    ):
        return self._get_or_create(
            GameCharacter,
            character_identity_id=character_identity_model.id,
            game_version_platform_id=game_version_platform_model.id
        )

    def _persist_duel(
        self: LegacyAggregatePersistence,
        duel: NormalizedDuelAggregate,
        event_model: Event,
        duel_type_model: DuelType,
        team_duel_type_model: DuelType,
        winner_player_model: Player,
        winner_team_model: Team
    ):
        if duel.duel.is_team_duel:
            winner_id = None
            winner_team_id = winner_team_model.id
        else:
            winner_id = winner_player_model.id
            winner_team_id = None

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
                "winner_id": winner_id,
                "winner_team_id": winner_team_id,
            }
        )

    def _persist_duel_participant(
        self,
        duel_model: Duel,
        player_model: Player
    ):
        return self._get_or_create(
            DuelParticipant,
            duel_id=duel_model.id,
            player_id=player_model.id
        )

    def _persist_duel_team(
        self,
        duel_model: Duel,
        team_model: Team
    ):
        return self._get_or_create(
            DuelTeam,
            duel_id=duel_model.id,
            team_id=team_model.id
        )

    def _persist_duel_team_member(
        self,
        duel_team_model: DuelTeam,
        player_model: Player
    ):
        return self._get_or_create(
            DuelTeamMember,
            duel_team_id=duel_team_model.id,
            player_id=player_model.id
        )

    # BATTLE persistence
    def _persist_stage(
        self: LegacyAggregatePersistence,
        battle: NormalizedBattleAggregate,
        game_version_platform_model: GameVersionPlatform
    ):
        return (
            self._get_or_create(
                Stage,
                name=battle.battle.stage_name,
                game_version_platform_id=game_version_platform_model.id
            )
        )

    def _persist_battle(
            self: LegacyAggregatePersistence,
            battle: NormalizedBattleAggregate,
            duel_model: Duel,
            stage_model: Stage,
            winner_model: Player,
            loser_model: Player
    ):
        winner_id = winner_model.id if winner_model else None
        loser_id = loser_model.id if loser_model else None

        return (
            self._get_or_create(
                Battle,
                duel_id=duel_model.id,
                stage_id=stage_model.id,
                winner_id=winner_id,
                loser_id=loser_id,
                sequence_number=battle.battle.battle_sequence_number,
                is_draw=battle.battle.is_draw
            )
        )

    def _persist_battle_participant(
        self: LegacyAggregatePersistence,
        position: int,
        battle_model: Battle,
        player_model: Player,
        game_character_model: GameCharacter,
        duel_team_model: DuelTeam
    ):
        duel_team_id = duel_team_model.id if duel_team_model else None

        return self._get_or_create(
            BattleParticipant,
            battle_id=battle_model.id,
            player_id=player_model.id,
            game_character_id=game_character_model.id,
            duel_team_id=duel_team_id,
            position=position
        )

    # ROUND persistence
    def _persist_round(
        self: LegacyAggregatePersistence,
        round: NormalizedRoundContext,
        battle_model: Battle,
        winner_model: Player,
        loser_model: Player
    ):
        winner_id = winner_model.id if winner_model else None
        loser_id = loser_model.id if loser_model else None

        return self._get_or_create(
            Round,
            battle_id=battle_model.id,
            winner_id=winner_id,
            loser_id=loser_id,
            is_draw=round.is_draw,
            sequence_number=round.round_sequence_number,
        )

    def _persist_round_result(
        self: LegacyAggregatePersistence,
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
