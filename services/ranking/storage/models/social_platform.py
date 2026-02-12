from sqlalchemy import Column, Integer, String, Index

from services.ranking.storage.base import Base


class SocialPlatform(Base):
    __tablename__ = "social_platforms"

    __table_args__ = (
        Index("ix_social_platforms_name", "name"),
    )

    id = Column(Integer, primary_key=True)

    # Fields
    name = Column(String, unique=True, nullable=False)
