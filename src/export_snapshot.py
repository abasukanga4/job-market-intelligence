"""Export a sanitized snapshot of the job-pipeline database for public analysis.

Reads the private pipeline DB (jobs.db), strips personal fields (resume-fit
reasoning, full descriptions, application notes), derives the posting date,
and writes a clean CSV the EDA notebook runs against.

Usage:
    python -m src.export_snapshot --db /path/to/jobs.db --out /reviewed/path/snapshot.csv
"""

import argparse
import json
import sqlite3
import tempfile
from pathlib import Path
from typing import Optional

import pandas as pd
from .analysis import read_snapshot, safe_cell

PUBLIC_COLUMNS = [
    "id",
    "source",
    "title",
    "company",
    "location",
    "workplace_type",
    "score",
    "status",
    "first_seen",
    "posted",
]


def derive_posted(raw_json: Optional[str]) -> Optional[str]:
    if not raw_json:
        return None
    try:
        return json.loads(raw_json).get("posted")
    except (json.JSONDecodeError, AttributeError):
        return None


def export(db_path: Path, out_path: Path) -> pd.DataFrame:
    if db_path.resolve() == out_path.resolve():
        raise ValueError('Output must not overwrite the database')
    con = sqlite3.connect(db_path.resolve().as_uri() + '?mode=ro', uri=True)
    try:
        jobs = pd.read_sql_query(
            "SELECT id, source, title, company, location, workplace_type, "
            "score, status, first_seen, raw_json FROM jobs ORDER BY id", con,
        )
    finally:
        con.close()

    jobs["posted"] = jobs["raw_json"].map(derive_posted)
    snapshot = jobs[PUBLIC_COLUMNS].copy()
    for column in snapshot.select_dtypes(include=['object']).columns:
        snapshot[column] = snapshot[column].map(lambda v: safe_cell(v) if isinstance(v, str) else v)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(dir=out_path.parent, suffix='.csv', delete=False) as temporary:
            temp_path = Path(temporary.name)
        snapshot.to_csv(temp_path, index=False)
        read_snapshot(temp_path)
        temp_path.replace(out_path)
    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)
    return snapshot


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, required=True)
    parser.add_argument("--out", type=Path, default=Path("data/jobs_snapshot.csv"))
    args = parser.parse_args()

    df = export(args.db, args.out)
    print(f"Exported {len(df)} postings -> {args.out}")
