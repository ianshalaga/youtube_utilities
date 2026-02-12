from sqlalchemy import (
    Column,
    Integer,
    ForeignKey,
    String,
    Index,
    UniqueConstraint,
    CheckConstraint,
)
from sqlalchemy.orm import relationship

from services.ranking.storage.base import Base
from services.ranking.storage.mixins import WithCode


class Duel(Base, WithCode):
    __tablename__ = "duels"

    __table_args__ = (
        Index("ix_duels_code", "code"),
        Index("ix_duels_event_id", "event_id"),
        Index("ix_duels_winner_id", "winner_id"),
        Index("ix_duels_winner_team_id", "winner_team_id"),
        UniqueConstraint("event_id", "sequence_number",
                         name="uq_duel_event_sequence"),
        CheckConstraint(
            """
            (winner_id IS NOT NULL AND winner_team_id IS NULL)
            OR
            (winner_id IS NULL AND winner_team_id IS NOT NULL)
            """,
            name="ck_duel_winner_consistency"
        ),
    )

    id = Column(Integer, primary_key=True)

    # Foreign keys
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False)
    duel_type_id = Column(Integer, ForeignKey("duel_types.id"), nullable=False)

    winner_id = Column(Integer, ForeignKey("players.id"), nullable=True)
    winner_team_id = Column(Integer, ForeignKey("teams.id"), nullable=True)

    # Fields
    sequence_number = Column(Integer, nullable=False)
    video_url = Column(String, nullable=True)

    # Relationships
    event = relationship("Event", back_populates="duels")
    duel_type = relationship("DuelType")
    winner = relationship("Player", foreign_keys=[winner_id])
    winner_team = relationship("Team", foreign_keys=[winner_team_id])

    duel_participants = relationship(
        "DuelParticipant",
        back_populates="duel",
        cascade="all, delete-orphan"
    )

    duel_teams = relationship(
        "DuelTeam",
        back_populates="duel",
        cascade="all, delete-orphan"
    )

    battles = relationship(
        "Battle",
        back_populates="duel",
        cascade="all, delete-orphan"
    )
