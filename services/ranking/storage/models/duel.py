import uuid
from sqlalchemy import Column, Integer, ForeignKey, String, Index
from services.ranking.storage.base import Base


class Duel(Base):
    __tablename__ = "duels"

    id = Column(Integer, primary_key=True)

    code = Column(
        String(36),
        unique=True,
        nullable=False,
        default=lambda: str(uuid.uuid4())
    )

    event_id = Column(Integer, ForeignKey("events.id"), nullable=False)
    duel_type_id = Column(Integer, ForeignKey("duel_types.id"), nullable=False)

    order = Column(Integer, nullable=False)

    video_url = Column(String, nullable=True)

    __table_args__ = (
        Index("ix_duels_code", "code"),
    )
