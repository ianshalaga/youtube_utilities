from sqlalchemy import Column, Integer, ForeignKey, UniqueConstraint, Index, CheckConstraint
from sqlalchemy.orm import relationship

from services.ranking.storage.base import Base


class BattleParticipant(Base):
    __tablename__ = "battle_participants"

    __table_args__ = (
        Index("ix_battle_participants_battle_id", "battle_id"),
        Index("ix_battle_participants_player_id", "player_id"),
        Index("ix_battle_participants_duel_team_id", "duel_team_id"),
        UniqueConstraint(
            "battle_id",
            "player_id",
            name="uq_battle_player"
        ),
        UniqueConstraint(
            "battle_id",
            "position",
            name="uq_battle_position"
        ),
        CheckConstraint(
            "position IN (1, 2)",
            name="ck_battle_participant_position_range"
        )
    )

    id = Column(Integer, primary_key=True)

    # Foreign Keys
    battle_id = Column(
        Integer,
        ForeignKey("battles.id", ondelete="CASCADE"),
        nullable=False
    )

    player_id = Column(
        Integer,
        ForeignKey("players.id", ondelete="RESTRICT"),
        nullable=False
    )

    game_character_id = Column(
        Integer,
        ForeignKey("game_characters.id", ondelete="RESTRICT"),
        nullable=False
    )

    duel_team_id = Column(
        Integer,
        ForeignKey("duel_teams.id", ondelete="RESTRICT"),
        nullable=True
    )

    # Fields
    position = Column(Integer, nullable=False)

    # Relationships
    battle = relationship("Battle", back_populates="battle_participants")
    player = relationship("Player")
    game_character = relationship("GameCharacter")
    duel_team = relationship("DuelTeam")
