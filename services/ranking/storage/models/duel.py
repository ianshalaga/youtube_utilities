from sqlalchemy import (
    Column,
    Integer,
    ForeignKey,
    String,
    Index,
    UniqueConstraint,
    CheckConstraint,
    Boolean
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
        Index("ix_duels_event_winner", "event_id", "winner_id"),
        UniqueConstraint(
            "event_id",
            "sequence_number",
            name="uq_duel_event_sequence"
        ),
        # UniqueConstraint(
        #     "event_id",
        #     "team_duel_sequence_number",
        #     name="uq_duel_event_team_sequence"
        # ),
        CheckConstraint(
            """
            (is_team_duel = TRUE AND winner_team_id IS NOT NULL AND winner_id IS NULL)
            OR
            (is_team_duel = FALSE AND winner_id IS NOT NULL AND winner_team_id IS NULL)
            """,
            name="ck_duel_type_winner_alignment"
        ),
        CheckConstraint(
            """
            (is_team_duel = TRUE AND team_duel_sequence_number IS NOT NULL)
            OR
            (is_team_duel = FALSE AND team_duel_sequence_number IS NULL)
            """,
            name="ck_duel_team_sequence_consistency"
        ),
        CheckConstraint(
            """
            (is_team_duel = TRUE AND team_duel_type_id IS NOT NULL)
            OR
            (is_team_duel = FALSE AND team_duel_type_id IS NULL)
            """,
            name="ck_duel_team_type_alignment"
        ),
        CheckConstraint(
            """
            (
                is_team_duel = FALSE
                AND duel_type_id IS NOT NULL
                AND team_duel_type_id IS NULL
            )
            OR
            (
                is_team_duel = TRUE
                AND duel_type_id IS NOT NULL
                AND team_duel_type_id IS NOT NULL
            )
            """,
            name="ck_duel_type_consistency"
        )
    )

    id = Column(Integer, primary_key=True)

    # Foreign keys
    event_id = Column(
        Integer,
        ForeignKey("events.id", ondelete="CASCADE"),
        nullable=False
    )

    duel_type_id = Column(
        Integer,
        ForeignKey("duel_types.id", ondelete="RESTRICT"),
        nullable=False
    )

    team_duel_type_id = Column(
        Integer,
        ForeignKey("duel_types.id", ondelete="RESTRICT"),
        nullable=True
    )

    winner_id = Column(
        Integer,
        ForeignKey("players.id", ondelete="RESTRICT"),
        nullable=True
    )

    winner_team_id = Column(
        Integer,
        ForeignKey("teams.id", ondelete="RESTRICT"),
        nullable=True
    )

    # Fields
    is_team_duel = Column(Boolean, nullable=False)
    sequence_number = Column(Integer, nullable=False)
    team_duel_sequence_number = Column(Integer, nullable=True)
    video_url = Column(String, nullable=True)

    # Relationships
    event = relationship("Event", back_populates="duels")
    duel_type = relationship("DuelType", foreign_keys=[duel_type_id])
    team_duel_type = relationship("DuelType", foreign_keys=[team_duel_type_id])
    winner = relationship("Player", foreign_keys=[winner_id])
    winner_team = relationship("Team", foreign_keys=[winner_team_id])

    duel_participants = relationship(
        "DuelParticipant",
        back_populates="duel",
        cascade="all, delete-orphan",
        passive_deletes=True
    )

    duel_teams = relationship(
        "DuelTeam",
        back_populates="duel",
        cascade="all, delete-orphan",
        passive_deletes=True
    )

    battles = relationship(
        "Battle",
        back_populates="duel",
        cascade="all, delete-orphan",
        passive_deletes=True
    )
