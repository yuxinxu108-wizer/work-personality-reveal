import argparse
import json
import sqlite3
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.repositories.jd_repository import JDRepository
from backend.app.services.evidence_service import build_evidence_summary


def analyze(db_path: Path) -> dict[str, object]:
    if not db_path.exists():
        raise RuntimeError(
            f"Database not found: {db_path}. "
            "Run scripts/import_jds.py --db data/app.db --seed-dir data/seeds first."
        )
    repository = JDRepository(db_path)
    try:
        directions = repository.list_directions()
    except sqlite3.Error as exc:
        raise RuntimeError(
            f"Database is not initialized: {db_path}. "
            "Run scripts/import_jds.py --db data/app.db --seed-dir data/seeds first."
        ) from exc
    if not directions:
        raise RuntimeError(
            f"Database has no directions: {db_path}. "
            "Run scripts/import_jds.py --db data/app.db --seed-dir data/seeds first."
        )
    return {
        direction["key"]: build_evidence_summary(repository, direction["key"])
        for direction in directions
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default="data/app.db")
    args = parser.parse_args()
    try:
        print(json.dumps(analyze(Path(args.db)), ensure_ascii=False, indent=2))
    except RuntimeError as exc:
        raise SystemExit(f"Cannot analyze keywords: {exc}") from exc


if __name__ == "__main__":
    main()
