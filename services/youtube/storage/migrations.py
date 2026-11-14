from sqlalchemy import Engine, inspect


_JOB_COLUMNS = {
    "name": "VARCHAR(255)",
    "first_publish_at": "VARCHAR(50)",
    "interval_days": "INTEGER",
    "timezone": "VARCHAR(100)",
}


def upgrade_schema(engine: Engine) -> None:
    """Add nullable job publication settings without replacing existing rows."""
    with engine.begin() as connection:
        existing_columns = {
            column["name"]
            for column in inspect(connection).get_columns("jobs")
        }

        for column_name, column_type in _JOB_COLUMNS.items():
            if column_name not in existing_columns:
                connection.exec_driver_sql(
                    f"ALTER TABLE jobs ADD COLUMN {column_name} "
                    f"{column_type} NULL"
                )
