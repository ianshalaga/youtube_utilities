from sqlalchemy import Column, Integer, ForeignKey, String
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy import Column, Integer, String
from sqlalchemy import Column, Integer, ForeignKey
from services.ranking.storage.base import Base


class BattleParticipant(Base):
    __tablename__ = "battle_participants"

    id = Column(Integer, primary_key=True)
    battle_id = Column(Integer, ForeignKey("battles.id"), nullable=False)
    player_id = Column(Integer, ForeignKey("players.id"), nullable=False)
    game_character_id = Column(Integer, ForeignKey(
        "game_characters.id"), nullable=False)


class Battle(Base):
    __tablename__ = "battles"

    id = Column(Integer, primary_key=True)
    duel_id = Column(Integer, ForeignKey("duels.id"), nullable=False)
    order = Column(Integer, nullable=False)


class CharacterIdentity(Base):
    __tablename__ = "character_identities"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    franchise = Column(String, nullable=False)


class Country(Base):
    __tablename__ = "countries"

    id = Column(Integer, primary_key=True)
    code = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)


class DuelParticipant(Base):
    __tablename__ = "duel_participants"

    id = Column(Integer, primary_key=True)
    duel_id = Column(Integer, ForeignKey("duels.id"), nullable=False)
    player_id = Column(Integer, ForeignKey("players.id"), nullable=False)


class Duel(Base):
    __tablename__ = "duels"

    id = Column(Integer, primary_key=True)
    event_id = Column(Integer, ForeignKey(
        "events.id"), nullable=False)
    order = Column(Integer, nullable=False)


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    platform_id = Column(Integer, ForeignKey("platforms.id"))
    game_id = Column(Integer, ForeignKey("games.id"))
    bracket_url = Column(String)
    playlist_url = Column(String)


class GameCharacter(Base):
    __tablename__ = "game_characters"

    id = Column(Integer, primary_key=True)
    character_identity_id = Column(
        Integer, ForeignKey("character_identities.id"), nullable=False
    )
    game_id = Column(Integer, ForeignKey("games.id"), nullable=False)
    game_version_id = Column(Integer, ForeignKey(
        "game_versions.id"), nullable=False)


class GameVersion(Base):
    __tablename__ = "game_versions"

    id = Column(Integer, primary_key=True)
    game_id = Column(Integer, ForeignKey("games.id"), nullable=False)
    version = Column(String, nullable=False)


class Game(Base):
    __tablename__ = "games"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)


class Platform(Base):
    __tablename__ = "platforms"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)


class Player(Base):
    __tablename__ = "players"

    id = Column(Integer, primary_key=True)
    nickname = Column(String, unique=True, nullable=False)
    country_id = Column(Integer, ForeignKey("countries.id"))


class RoundResult(Base):
    __tablename__ = "round_results"

    id = Column(Integer, primary_key=True)
    round_id = Column(Integer, ForeignKey("rounds.id"), nullable=False)
    player_id = Column(Integer, ForeignKey("players.id"), nullable=False)

    # W, LB, LY, PW, PL, D, 0
    result_code = Column(String, nullable=False)


class Round(Base):
    __tablename__ = "rounds"

    id = Column(Integer, primary_key=True)
    battle_id = Column(Integer, ForeignKey("battles.id"), nullable=False)
    order = Column(Integer, nullable=False)
