from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint
from services.ranking.storage.base import Base


class PlayerAlias(Base):
    __tablename__ = "player_aliases"

    id = Column(Integer, primary_key=True)

    player_id = Column(Integer, ForeignKey("players.id"), nullable=False)

    alias = Column(String, nullable=False)

    __table_args__ = (
        UniqueConstraint("player_id", "alias"),
    )
