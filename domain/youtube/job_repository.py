from typing import Protocol

from domain.youtube.job import Job


class JobRepository(Protocol):
    def find_selectable(self) -> list[Job]:
        ...

    def find_by_id(self, job_id: int) -> Job | None:
        ...

    def find_pending(self) -> Job | None:
        ...

    def find_failed(self) -> Job | None:
        ...

    def save(self, job: Job) -> None:
        ...

    def delete_completed(self) -> None:
        ...

    def delete(self, job: Job) -> None:
        ...
