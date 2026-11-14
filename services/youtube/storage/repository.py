from sqlalchemy import select
from sqlalchemy.orm import Session

from domain.youtube.job import Job, JobStatus
from domain.youtube.job_repository import JobRepository

from services.youtube.storage.mappers.job_mapper import JobMapper
from services.youtube.storage.models.job import JobModel


class YouTubeJobRepository(JobRepository):

    def __init__(self, session: Session, mapper: JobMapper):
        self._session = session
        self._mapper = mapper

    def find_selectable(self) -> list[Job]:
        selectable_statuses = (
            JobStatus.CREATED.value,
            JobStatus.FAILED.value,
            JobStatus.PENDING.value,
            JobStatus.RUNNING.value,
        )
        statement = (
            select(JobModel)
            .where(JobModel.status.in_(selectable_statuses))
            .order_by(JobModel.id)
        )
        return [
            self._mapper.to_domain(job_model)
            for job_model in self._session.scalars(statement).all()
        ]

    def find_by_id(self, job_id: int) -> Job | None:
        job_model = self._session.get(JobModel, job_id)
        if job_model is None:
            return None
        return self._mapper.to_domain(job_model)

    def find_pending(self) -> Job | None:
        statement = (
            select(JobModel)
            .where(JobModel.status == "pending")
            .order_by(JobModel.id)
            .limit(1)
        )

        job_model = self._session.scalars(statement).first()
        return self._mapper.to_domain(job_model) if job_model else None

    def find_failed(self) -> Job | None:
        statement = (
            select(JobModel)
            .where(JobModel.status == "failed")
            .order_by(JobModel.id)
            .limit(1)
        )

        job_model = self._session.scalars(statement).first()
        return self._mapper.to_domain(job_model) if job_model else None

    def save(self, job: Job) -> None:
        new_job_id = None
        try:
            if job.id is not None:
                job_model = self._session.get(JobModel, job.id)
                if job_model is None:
                    raise ValueError(f"Job with ID {job.id} does not exist.")
                self._mapper.update_model(job_model, job)
            else:
                job_model = self._mapper.to_model(job)
                self._session.add(job_model)
                self._session.flush()
                new_job_id = job_model.id

            self._session.commit()
        except Exception:
            self._session.rollback()
            raise

        if new_job_id is not None:
            job.assign_id(new_job_id)

    def delete(self, job: Job) -> None:
        if job.id is None:
            raise ValueError("Only a persisted job can be deleted.")
        if job.status not in {JobStatus.FAILED, JobStatus.RUNNING}:
            raise ValueError("Only failed or running jobs can be deleted.")
        job_model = self._session.get(JobModel, job.id)
        if job_model is None:
            raise ValueError(f"Job with ID {job.id} does not exist.")
        try:
            self._session.delete(job_model)
            self._session.commit()
        except Exception:
            self._session.rollback()
            raise
