import uuid
from sqlalchemy import Column, Integer, ForeignKey, String
from services.ranking.storage.base import Base


class GameCharacter(Base):
    __tablename__ = "game_characters"

    id = Column(Integer, primary_key=True)

    code = Column(
        String(36),
        unique=True,
        nullable=False,
        default=lambda: str(uuid.uuid4())
    )

    character_identity_id = Column(Integer, ForeignKey(
        "character_identities.id"), nullable=False)
    game_version_id = Column(Integer, ForeignKey(
        "game_versions.id"), nullable=False)
