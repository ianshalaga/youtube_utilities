import uuid
from sqlalchemy import Column, Integer, String, Index
from services.ranking.storage.base import Base


class Country(Base):
    __tablename__ = "countries"

    id = Column(Integer, primary_key=True)

    code = Column(
        String(36),
        unique=True,
        nullable=False,
        default=lambda: str(uuid.uuid4())
    )

    iso_code = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)

    __table_args__ = (
        Index("ix_countries_code", "code"),
    )
