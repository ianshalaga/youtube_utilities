import uuid
from sqlalchemy import Column, Integer, String
from services.ranking.storage.base import Base


class Region(Base):
    __tablename__ = "regions"

    id = Column(Integer, primary_key=True)

    code = Column(
        String(36),
        unique=True,
        nullable=False,
        default=lambda: str(uuid.uuid4())
    )

    name = Column(String, unique=True, nullable=False)
