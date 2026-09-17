from typing import Protocol

from domain.youtube.job import Job


class JobRepository(Protocol):
    def find_pending(self) -> Job | None:
        ...

    def find_failed(self) -> Job | None:
        ...

    def save(self, job: Job) -> None:
        ...