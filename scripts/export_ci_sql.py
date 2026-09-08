from __future__ import annotations

import json
import sys
from pathlib import Path


def sql_text(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def main(source_jsonl: Path, destination: Path) -> None:
    document = json.loads(source_jsonl.read_text(encoding="utf-8").splitlines()[0])
    rows = document["rows"]
    header = rows[0]
    records = [dict(zip(header, row)) for row in rows[1:]]

    lines = [
        "CREATE TABLE IF NOT EXISTS ci_runs (",
        "  week integer NOT NULL CHECK (week BETWEEN 1 AND 8),",
        "  run_id text PRIMARY KEY,",
        "  change_size text NOT NULL CHECK (change_size IN ('S','M','L','XL')),",
        "  checks_count integer NOT NULL,",
        "  queue_duration_min numeric(8,1) NOT NULL,",
        "  execution_duration_min numeric(8,1) NOT NULL,",
        "  total_duration_min numeric(8,1) NOT NULL,",
        "  status text NOT NULL CHECK (status IN ('success','failed','cancelled')),",
        "  slowest_check_type text NOT NULL",
        ");",
        "",
        "INSERT INTO ci_runs (week, run_id, change_size, checks_count, queue_duration_min, execution_duration_min, total_duration_min, status, slowest_check_type) VALUES",
    ]
    values = []
    for row in records:
        values.append(
            "(" + ", ".join([
                str(row["week"]),
                sql_text(row["run_id"]),
                sql_text(row["change_size"]),
                str(row["checks_count"]),
                str(row["queue_duration_min"]),
                str(row["execution_duration_min"]),
                str(row["total_duration_min"]),
                sql_text(row["status"]),
                sql_text(row["slowest_check_type"]),
            ]) + ")"
        )
    lines.append(",\n".join(values) + "\nON CONFLICT (run_id) DO NOTHING;")
    lines.extend([
        "",
        "CREATE INDEX IF NOT EXISTS ci_runs_week_idx ON ci_runs (week);",
        "CREATE INDEX IF NOT EXISTS ci_runs_filters_idx ON ci_runs (change_size, status);",
        "ANALYZE ci_runs;",
        "",
    ])
    destination.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]))
