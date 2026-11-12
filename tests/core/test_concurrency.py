import pytest

from core import concurrency


@pytest.mark.parametrize(
    ("cpu_count", "task_count", "worker_limit", "expected"),
    [
        (8, 20, None, 7),
        (8, 3, None, 3),
        (8, 20, 4, 4),
        (1, 5, None, 1),
        (None, 5, None, 1),
    ],
)
def test_calculate_max_workers_respects_available_limits(
    monkeypatch,
    cpu_count: int | None,
    task_count: int,
    worker_limit: int | None,
    expected: int,
) -> None:
    monkeypatch.setattr(concurrency.os, "cpu_count", lambda: cpu_count)

    assert concurrency.calculate_max_workers(
        task_count,
        worker_limit=worker_limit,
    ) == expected


def test_calculate_max_workers_returns_zero_without_tasks() -> None:
    assert concurrency.calculate_max_workers(0) == 0


@pytest.mark.parametrize(
    ("task_count", "worker_limit", "message"),
    [
        (-1, None, "task_count"),
        (1, 0, "worker_limit"),
    ],
)
def test_calculate_max_workers_rejects_invalid_limits(
    task_count: int,
    worker_limit: int | None,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        concurrency.calculate_max_workers(
            task_count,
            worker_limit=worker_limit,
        )
