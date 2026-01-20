import uuid
from sqlalchemy import Column, Integer, String, Index
from services.ranking.storage.base import Base


class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True)

    code = Column(
        String(36),
        unique=True,
        nullable=False,
        default=lambda: str(uuid.uuid4())
    )

    name = Column(String, nullable=True)

    __table_args__ = (
        Index("ix_teams_code", "code"),
    )
