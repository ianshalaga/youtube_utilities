from sqlalchemy import Column, Integer, String
from services.ranking.storage.base import Base


class SocialPlatform(Base):
    __tablename__ = "social_platforms"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
