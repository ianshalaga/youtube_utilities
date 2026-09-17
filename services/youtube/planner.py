# services/youtube/planner.py

from domain.youtube.album import Album
from domain.youtube.job import Job
from services.youtube.operations_builder import OperationsBuilder


class Planner:
    """
    Creates an executable Job from an Album.

    The Album represents the desired state. The OperationsBuilder
    decomposes that desired state into concrete operations, while the
    Planner groups those operations into a Job without executing them.

    A newly planned Job starts in PENDING. The Updater changes it to RUNNING
    when execution begins. If YouTube quota is exhausted, the Updater returns
    the Job to PENDING so it can be resumed on a later execution.
    """

    def __init__(self, operations_builder: OperationsBuilder) -> None:
        self._operations_builder = operations_builder

    def plan(self, album: Album) -> Job:
        operations = self._operations_builder.build(album)
        return Job(operations)
