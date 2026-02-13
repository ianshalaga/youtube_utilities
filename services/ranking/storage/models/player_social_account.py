from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from services.ranking.storage.base import Base


class PlayerSocialAccount(Base):
    __tablename__ = "player_social_accounts"

    __table_args__ = (
        UniqueConstraint("social_platform_id", "handle",
                         name="uq_player_social_account"),
    )

    id = Column(Integer, primary_key=True)

    # Foreign Keys
    player_id = Column(
        Integer,
        ForeignKey("players.id", ondelete="CASCADE"),
        nullable=False
    )

    social_platform_id = Column(
        Integer,
        ForeignKey("social_platforms.id", ondelete="RESTRICT"),
        nullable=False
    )

    # Fields
    handle = Column(String, nullable=False)

    # Relationships
    player = relationship("Player", back_populates="social_accounts")
    social_platform = relationship("SocialPlatform")
