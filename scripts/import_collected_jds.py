import argparse
import csv
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.db import connect, initialize_database
from backend.app.services.jd_collection_service import normalize_collection_row


def import_collected_jds(db_path: Path, csv_path: Path) -> int:
    initialize_database(db_path)
    count = 0

    with csv_path.open(newline="", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        with connect(db_path) as conn:
            for row_number, row in enumerate(reader, start=2):
                jd = normalize_collection_row(row, row_number=row_number)
                conn.execute(
                    """
                    INSERT INTO jd_sources (
                      id, company, role_title, role_category, source_url, source_type,
                      source_quality, collector_notes, raw_status, location,
                      employment_type, raw_text, responsibilities_text,
                      requirements_text, collected_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET
                      company = excluded.company,
                      role_title = excluded.role_title,
                      role_category = excluded.role_category,
                      source_type = excluded.source_type,
                      source_quality = excluded.source_quality,
                      collector_notes = excluded.collector_notes,
                      raw_status = excluded.raw_status,
                      location = excluded.location,
                      employment_type = excluded.employment_type,
                      raw_text = excluded.raw_text,
                      responsibilities_text = excluded.responsibilities_text,
                      requirements_text = excluded.requirements_text,
                      collected_at = excluded.collected_at
                    WHERE jd_sources.raw_status IN ('collected', 'ai_annotated')
                    """,
                    (
                        jd["id"],
                        jd["company"],
                        jd["role_title"],
                        jd["role_category"],
                        jd["source_url"],
                        jd["source_type"],
                        jd["source_quality"],
                        jd["collector_notes"],
                        jd["raw_status"],
                        jd["location"],
                        jd["employment_type"],
                        jd["raw_text"],
                        jd["responsibilities_text"],
                        jd["requirements_text"],
                        jd["collected_at"],
                    ),
                )
                count += 1

    return count


def main() -> None:
    parser = argparse.ArgumentParser(description="Import collected JD CSV records.")
    parser.add_argument("--db", required=True, type=Path)
    parser.add_argument("--csv", required=True, type=Path)
    args = parser.parse_args()

    count = import_collected_jds(args.db, args.csv)
    print(f"Imported {count} collected JD records into {args.db}")


if __name__ == "__main__":
    main()
