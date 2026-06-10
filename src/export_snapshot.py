"""Export a sanitized snapshot of the job-pipeline database for public analysis.

Reads the private pipeline DB (jobs.db), strips personal fields (resume-fit
reasoning, full descriptions, application notes), derives the posting date,
and writes a clean CSV the EDA notebook runs against.

Usage:
    python3 src/export_snapshot.py --db /path/to/jobs.db --out data/jobs_snapshot.csv
"""

import argparse
import json
import sqlite3
from pathlib import Path
from typing import Optional

import pandas as pd

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
    con = sqlite3.connect(db_path)
    jobs = pd.read_sql_query(
        "SELECT id, source, title, company, location, workplace_type, "
        "score, status, first_seen, raw_json FROM jobs",
        con,
    )
    con.close()

    jobs["posted"] = jobs["raw_json"].map(derive_posted)
    snapshot = jobs[PUBLIC_COLUMNS].copy()

    out_path.parent.mkdir(parents=True, exist_ok=True)
    snapshot.to_csv(out_path, index=False)
    return snapshot


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, required=True)
    parser.add_argument("--out", type=Path, default=Path("data/jobs_snapshot.csv"))
    args = parser.parse_args()

    df = export(args.db, args.out)
    print(f"Exported {len(df)} postings -> {args.out}")
