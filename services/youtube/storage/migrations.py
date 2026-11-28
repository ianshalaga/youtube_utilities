from sqlalchemy import Connection, Engine, inspect


_JOB_COLUMNS = {
    "name": "VARCHAR(255)",
    "first_publish_at": "VARCHAR(50)",
    "interval_days": "INTEGER",
    "timezone": "VARCHAR(100)",
}


def upgrade_schema(engine: Engine) -> None:
    """Apply incremental schema upgrades without replacing existing rows."""
    with engine.begin() as connection:
        inspector = inspect(connection)

        existing_job_columns = {
            column["name"]
            for column in inspector.get_columns("jobs")
        }

        for column_name, column_type in _JOB_COLUMNS.items():
            if column_name not in existing_job_columns:
                connection.exec_driver_sql(
                    f"ALTER TABLE jobs ADD COLUMN {column_name} "
                    f"{column_type} NULL"
                )

        if "videos" not in inspector.get_table_names():
            return

        video_columns = {
            column["name"]
            for column in inspector.get_columns("videos")
        }
        if "job_id" not in video_columns:
            _assign_videos_to_jobs(connection)
            _delete_orphan_video_metadatas(connection)

    _ensure_auto_vacuum(engine)


def _ensure_auto_vacuum(engine: Engine) -> None:
    """Enable FULL auto-vacuum so deleted rows shrink the database file."""
    with engine.connect().execution_options(
        isolation_level="AUTOCOMMIT"
    ) as connection:
        auto_vacuum = connection.exec_driver_sql(
            "PRAGMA auto_vacuum"
        ).scalar()
        if auto_vacuum == 1:
            return
        connection.exec_driver_sql("PRAGMA auto_vacuum=FULL")
        connection.exec_driver_sql("VACUUM")


def _assign_videos_to_jobs(connection: Connection) -> None:
    """Rebuild videos with job ownership, keeping only referenced rows."""
    connection.exec_driver_sql(
        """
        CREATE TABLE videos_migrated (
            id INTEGER NOT NULL,
            job_id INTEGER NOT NULL,
            video_id VARCHAR(20) NOT NULL,
            position INTEGER NOT NULL,
            video_type VARCHAR(20) NOT NULL,
            PRIMARY KEY (id),
            FOREIGN KEY(job_id) REFERENCES jobs (id),
            UNIQUE (job_id, video_id)
        )
        """
    )
    connection.exec_driver_sql(
        """
        INSERT INTO videos_migrated
            (id, job_id, video_id, position, video_type)
        SELECT
            v.id,
            MIN(o.job_id),
            v.video_id,
            v.position,
            v.video_type
        FROM videos v
        JOIN operations o ON o.video_id = v.id
        GROUP BY v.id
        """
    )
    connection.exec_driver_sql("DROP TABLE videos")
    connection.exec_driver_sql(
        "ALTER TABLE videos_migrated RENAME TO videos"
    )


def _delete_orphan_video_metadatas(connection: Connection) -> None:
    """Remove metadata rows not referenced by any operation."""
    connection.exec_driver_sql(
        """
        DELETE FROM video_metadatas
        WHERE id NOT IN (SELECT data_id FROM operations)
        """
    )
