from pathlib import Path

from services.ranking.storage.session import SessionLocal
from services.ranking.loaders.legacy.csv_loader_legacy import CsvLegacyLoader


def run(csv_path: str):
    with SessionLocal() as session:
        loader = CsvLegacyLoader(session)

        with session.begin():
            loader.load(Path(csv_path))
