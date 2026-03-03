from sqlalchemy import Column, Integer, String, ForeignKey, Index
from sqlalchemy.orm import relationship

from services.ranking.storage.base import Base
from services.ranking.storage.mixins import WithCode


class Player(Base, WithCode):
    __tablename__ = "players"

    __table_args__ = (
        Index("ix_players_code", "code"),
    )

    id = Column(Integer, primary_key=True)

    # Foreign Keys
    country_id = Column(
        Integer,
        ForeignKey("countries.id", ondelete="RESTRICT"),
        nullable=False
    )

    # Fields
    canonical_name = Column(String, unique=True, nullable=False)
    display_name = Column(String, nullable=False)

    # Relationships
    country = relationship("Country")
    aliases = relationship("PlayerAlias", back_populates="player")
    social_accounts = relationship(
        "PlayerSocialAccount", back_populates="player")
