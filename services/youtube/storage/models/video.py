from sqlalchemy import Column, Integer, String

from services.youtube.storage.base import Base


class VideoModel(Base):
    __tablename__ = "videos"

    id = Column(Integer, primary_key=True)

    video_id = Column(String(20), nullable=False, unique=True)
    position = Column(Integer, nullable=False, unique=True)
    video_type = Column(String(20), nullable=False)