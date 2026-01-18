from sqlalchemy import Column, Integer, String, Date, ForeignKey
from services.ranking.storage.base import Base


class PlayerSocialAccount(Base):
    __tablename__ = "player_social_accounts"

    id = Column(Integer, primary_key=True)
    player_id = Column(Integer, ForeignKey("players.id"), nullable=False)
    platform_id = Column(Integer, ForeignKey(
        "social_platforms.id"), nullable=False)
    handle = Column(String, nullable=False)
