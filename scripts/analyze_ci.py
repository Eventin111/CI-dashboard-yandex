from __future__ import annotations

import json
import statistics
from collections import Counter, defaultdict
from pathlib import Path


def percentile(values, q):
    values = sorted(values)
    if not values:
        return None
    pos = (len(values) - 1) * q
    lo = int(pos)
    hi = min(lo + 1, len(values) - 1)
    return values[lo] + (values[hi] - values[lo]) * (pos - lo)


docs = [json.loads(line) for line in Path("/tmp/ci_workbook.jsonl").read_text().splitlines()]
rows = docs[0]["rows"]
header = rows[0]
data = [dict(zip(header, row)) for row in rows[1:]]

print("OVERALL")
completed = [row for row in data if row["status"] != "cancelled"]
print("runs", len(data), "completed", len(completed))
print("success rate", sum(row["status"] == "success" for row in completed) / len(completed))
for field in ["queue_duration_min", "execution_duration_min", "total_duration_min"]:
    vals = [row[field] for row in completed]
    print(field, "median", statistics.median(vals), "p90", percentile(vals, .9))

print("\nWEEKS")
for week in range(1, 9):
    part = [row for row in data if row["week"] == week and row["status"] != "cancelled"]
    print(week, {
        "n": len(part),
        "success_rate": round(sum(row["status"] == "success" for row in part) / len(part), 4),
        "median_total": statistics.median(row["total_duration_min"] for row in part),
        "median_queue": statistics.median(row["queue_duration_min"] for row in part),
        "median_execution": statistics.median(row["execution_duration_min"] for row in part),
        "p90_total": round(percentile([row["total_duration_min"] for row in part], .9), 2),
    })

print("\nFAILURE PROXY")
print(Counter(row["slowest_check_type"] for row in data if row["status"] == "failed"))

print("\nBY SIZE COMPLETED")
for size in ["S", "M", "L", "XL"]:
    part = [row for row in completed if row["change_size"] == size]
    print(size, len(part), "success", round(sum(row["status"] == "success" for row in part) / len(part), 3),
          "median total", statistics.median(row["total_duration_min"] for row in part),
          "p90", round(percentile([row["total_duration_min"] for row in part], .9), 1),
          "median queue", statistics.median(row["queue_duration_min"] for row in part))

print("\nSLOWEST TYPE COMPLETED")
for check in sorted(set(row["slowest_check_type"] for row in completed)):
    part = [row for row in completed if row["slowest_check_type"] == check]
    print(check, len(part), "median total", statistics.median(row["total_duration_min"] for row in part),
          "median execution", statistics.median(row["execution_duration_min"] for row in part))

print("\nCANCELLED")
part = [row for row in data if row["status"] == "cancelled"]
print(len(part), statistics.median(row["total_duration_min"] for row in part), min(row["total_duration_min"] for row in part), max(row["total_duration_min"] for row in part))

print("\nCOMPACT_DATA")
keys = ["week", "run_id", "change_size", "checks_count", "queue_duration_min", "execution_duration_min", "total_duration_min", "status", "slowest_check_type"]
print(json.dumps([[row[key] for key in keys] for row in data], ensure_ascii=False, separators=(",", ":")))
