from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from services.youtube.storage.base import Base


class JobModel(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True)

    status = Column(String(20), nullable=False)

    operations = relationship(
        "OperationModel",
        back_populates="job",
        cascade="all, delete-orphan",
    )