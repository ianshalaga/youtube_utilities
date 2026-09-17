from sqlalchemy.orm import Session

from domain.youtube.job import Job
from domain.youtube.job_repository import JobRepository


class YouTubeJobRepository(JobRepository):

    def __init__(self, session: Session):
            self._session = session

    def find_pending(self) -> Job | None:
        ...

    def find_failed(self) -> Job | None:
        ...

    def save(self, job: Job) -> None:
        ...