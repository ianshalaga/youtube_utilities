from pathlib import Path

from services.ranking.loaders.csv_loader_legacy import CSVLoaderLegacy


def run(csv_path: str):
    loader = CSVLoaderLegacy(Path(csv_path))
    loader.load()
