from sqlalchemy import create_engine, inspect, text

from services.youtube.storage.base import Base
from services.youtube.storage import models
from services.youtube.storage.migrations import upgrade_schema


def test_all_tables_are_registered():
    engine = create_engine("sqlite:///:memory:")

    Base.metadata.create_all(engine)

    inspector = inspect(engine)

    assert set(inspector.get_table_names()) == {
        "jobs",
        "operations",
        "videos",
        "video_metadatas",
    }


def test_operation_foreign_keys_are_defined():
    engine = create_engine("sqlite:///:memory:")

    Base.metadata.create_all(engine)

    inspector = inspect(engine)

    foreign_keys = inspector.get_foreign_keys("operations")

    assert {
        (foreign_key["constrained_columns"][0], foreign_key["referred_table"])
        for foreign_key in foreign_keys
    } == {
        ("job_id", "jobs"),
        ("video_id", "videos"),
        ("data_id", "video_metadatas"),
    }


def test_upgrade_schema_adds_publication_columns_without_losing_jobs():
    engine = create_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        connection.execute(
            text(
                "CREATE TABLE jobs "
                "(id INTEGER PRIMARY KEY, status VARCHAR(20) NOT NULL)"
            )
        )
        connection.execute(
            text("INSERT INTO jobs (id, status) VALUES (48, 'pending')")
        )

    upgrade_schema(engine)
    columns = {column["name"] for column in inspect(engine).get_columns("jobs")}
    with engine.connect() as connection:
        job = connection.execute(
            text("SELECT id, status FROM jobs WHERE id = 48")
        ).one()

    assert {"name", "first_publish_at", "interval_days", "timezone"} <= columns
    assert tuple(job) == (48, "pending")


def test_job_has_operations_relationship():
    assert hasattr(models.JobModel, "operations")


def test_operation_has_job_relationship():
    assert hasattr(models.OperationModel, "job")


def test_operation_has_video_relationship():
    assert hasattr(models.OperationModel, "video")


def test_operation_has_data_relationship():
    assert hasattr(models.OperationModel, "data")
