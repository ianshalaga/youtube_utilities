from sqlalchemy import select
from sqlalchemy.orm import Session

from domain.youtube.job import Job
from domain.youtube.job_repository import JobRepository

from services.youtube.storage.mappers.job_mapper import JobMapper
from services.youtube.storage.models.job import JobModel


class YouTubeJobRepository(JobRepository):

    def __init__(self, session: Session, mapper: JobMapper):
        self._session = session
        self._mapper = mapper
        self._current_job_model: JobModel | None = None

    def find_pending(self) -> Job | None:
        statement = (
            select(JobModel)
            .where(JobModel.status == "pending")
            .order_by(JobModel.id)
            .limit(1)
        )

        job_model = self._session.scalars(statement).first()

        if job_model is None:
            return None

        self._current_job_model = job_model
        return self._mapper.to_domain(job_model)

    def find_failed(self) -> Job | None:
        statement = (
            select(JobModel)
            .where(JobModel.status == "failed")
            .order_by(JobModel.id)
            .limit(1)
        )

        job_model = self._session.scalars(statement).first()

        if job_model is None:
            return None

        self._current_job_model = job_model
        return self._mapper.to_domain(job_model)

    def save(self, job: Job) -> None:
        if self._current_job_model is not None:
            self._mapper.update_model(self._current_job_model, job)
        else:
            self._current_job_model = self._mapper.to_model(job)
            self._session.add(self._current_job_model)

        self._session.commit()
        self._current_job_model = None