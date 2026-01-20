import uuid
from sqlalchemy import Column, Integer, String
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
