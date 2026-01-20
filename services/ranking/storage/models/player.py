import uuid
from sqlalchemy import Column, Integer, String, ForeignKey, Index
from services.ranking.storage.base import Base


class Player(Base):
    __tablename__ = "players"

    id = Column(Integer, primary_key=True)

    code = Column(
        String(36),
        unique=True,
        nullable=False,
        default=lambda: str(uuid.uuid4())
    )

    country_id = Column(Integer, ForeignKey("countries.id"))

    nickname = Column(String, unique=True, nullable=False)

    __table_args__ = (
        Index("ix_players_code", "code"),
    )
