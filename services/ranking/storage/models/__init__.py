"""
Carga explícita de todos los modelos ORM.

Este archivo existe exclusivamente para garantizar que
todas las clases que heredan de Base sean registradas
en Base.metadata antes de ejecutar create_all().
"""

from services.ranking.storage.models.country import Country
from services.ranking.storage.models.platform import Platform
from services.ranking.storage.models.game import Game
from services.ranking.storage.models.game_version import GameVersion
from services.ranking.storage.models.character_identity import CharacterIdentity
from services.ranking.storage.models.game_character import GameCharacter
from services.ranking.storage.models.player import Player
from services.ranking.storage.models.event import Event
from services.ranking.storage.models.duel import Duel
from services.ranking.storage.models.duel_participant import DuelParticipant
from services.ranking.storage.models.battle import Battle
from services.ranking.storage.models.battle_participant import BattleParticipant
from services.ranking.storage.models.round import Round
from services.ranking.storage.models.round_result import RoundResult
