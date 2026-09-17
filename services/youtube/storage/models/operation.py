from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from services.youtube.storage.base import Base


class OperationModel(Base):
    __tablename__ = "operations"

    id = Column(Integer, primary_key=True)

    job_id = Column(
        Integer,
        ForeignKey("jobs.id"),
        nullable=False,
    )

    video_id = Column(
        Integer,
        ForeignKey("videos.id"),
        nullable=False,
    )

    data_id = Column(
        Integer,
        ForeignKey("video_metadatas.id"),
        nullable=False,
    )

    operation_type = Column(String(50), nullable=False)
    status = Column(String(20), nullable=False)

    job = relationship(
        "JobModel",
        back_populates="operations",
    )

    video = relationship(
        "VideoModel",
    )

    data = relationship(
        "VideoMetadataModel",
        uselist=False,
    )