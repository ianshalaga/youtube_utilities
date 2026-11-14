from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from services.youtube.storage.base import Base


class JobModel(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True)

    status = Column(String(20), nullable=False)

    name = Column(String(255), nullable=True)
    first_publish_at = Column(String(50), nullable=True)
    interval_days = Column(Integer, nullable=True)
    timezone = Column(String(100), nullable=True)

    operations = relationship(
        "OperationModel",
        back_populates="job",
        cascade="all, delete-orphan",
    )
