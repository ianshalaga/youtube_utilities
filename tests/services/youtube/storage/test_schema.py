from sqlalchemy import create_engine, inspect

from services.youtube.storage.base import Base
from services.youtube.storage import models


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


def test_job_has_operations_relationship():
    assert hasattr(models.JobModel, "operations")


def test_operation_has_job_relationship():
    assert hasattr(models.OperationModel, "job")


def test_operation_has_video_relationship():
    assert hasattr(models.OperationModel, "video")


def test_operation_has_data_relationship():
    assert hasattr(models.OperationModel, "data")