from sqlalchemy import Column, Integer, String, Index

from services.ranking.storage.base import Base


class DuelType(Base):
    __tablename__ = "duel_types"

    __table_args__ = (
        Index("ix_duel_types_name", "name"),
    )

    id = Column(Integer, primary_key=True)

    # Fields
    name = Column(String, unique=True, nullable=False)
