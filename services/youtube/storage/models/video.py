from sqlalchemy import Column, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship

from services.youtube.storage.base import Base


class VideoModel(Base):
    __tablename__ = "videos"
    __table_args__ = (
        UniqueConstraint("job_id", "video_id"),
    )

    id = Column(Integer, primary_key=True)

    job_id = Column(
        Integer,
        ForeignKey("jobs.id"),
        nullable=False,
    )

    video_id = Column(String(20), nullable=False)
    position = Column(Integer, nullable=False)
    video_type = Column(String(20), nullable=False)

    job = relationship(
        "JobModel",
        back_populates="videos",
    )
