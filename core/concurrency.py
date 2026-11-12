"""Utilities for limiting concurrent work to available CPU capacity."""

import os


def calculate_max_workers(
    task_count: int,
    *,
    worker_limit: int | None = None,
) -> int:
    """Return a suitable worker count for the number of pending tasks.

    The calculation reserves one logical CPU for the rest of the system and
    never creates more workers than tasks. An optional limit can impose a
    lower, application-specific cap.
    """
    if task_count < 0:
        raise ValueError("task_count no puede ser negativo.")
    if worker_limit is not None and worker_limit <= 0:
        raise ValueError("worker_limit debe ser mayor que cero.")
    if task_count == 0:
        return 0

    cpu_workers = max(1, (os.cpu_count() or 1) - 1)
    limits = [cpu_workers, task_count]
    if worker_limit is not None:
        limits.append(worker_limit)

    return min(limits)
