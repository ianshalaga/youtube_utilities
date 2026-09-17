from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text

from services.youtube.storage.base import Base


class VideoMetadataModel(Base):
    __tablename__ = "video_metadatas"

    id = Column(Integer, primary_key=True)

    title = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)
    tags = Column(Text, nullable=True)
    game = Column(String(255), nullable=True)

    made_for_kids = Column(Boolean, nullable=True)
    contains_synthetic_media = Column(Boolean, nullable=True)

    publish_at = Column(DateTime, nullable=True)
    thumbnail = Column(String(1024), nullable=True)

    playlist = Column(String(255), nullable=True)