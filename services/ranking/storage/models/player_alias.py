from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from services.ranking.storage.base import Base


class PlayerAlias(Base):
    __tablename__ = "player_aliases"

    __table_args__ = (
        UniqueConstraint("player_id", "alias"),
    )

    id = Column(Integer, primary_key=True)

    # Foreign Keys
    player_id = Column(Integer, ForeignKey("players.id"), nullable=False)

    # Fields
    alias = Column(String, nullable=False)

    # Relationships
    player = relationship("Player", back_populates="aliases")
