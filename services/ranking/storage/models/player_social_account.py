from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from services.ranking.storage.base import Base


class PlayerSocialAccount(Base):
    __tablename__ = "player_social_accounts"

    __table_args__ = (
        UniqueConstraint("platform_id", "handle"),
    )

    id = Column(Integer, primary_key=True)

    # Foreign Keys
    player_id = Column(Integer, ForeignKey("players.id"), nullable=False)
    social_platform_id = Column(Integer, ForeignKey(
        "social_platforms.id"), nullable=False)

    # Fields
    handle = Column(String, nullable=False)

    # Relationships
    player = relationship("Player", back_populates="social_accounts")
    social_platform = relationship("SocialPlatform")
