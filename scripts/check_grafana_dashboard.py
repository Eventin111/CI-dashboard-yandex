from __future__ import annotations

import json
import sys
from pathlib import Path
from urllib.request import Request, urlopen


def main(dashboard_path: Path, base_url: str) -> None:
    dashboard = json.loads(dashboard_path.read_text(encoding="utf-8"))
    replacements = {
        "${week:csv}": "1,2,3,4,5,6,7,8",
        "${change_size:sqlstring}": "'S','M','L','XL'",
        "${run_status:sqlstring}": "'success','failed'",
    }
    failures = []
    checked = 0
    for panel in dashboard["panels"]:
        for target in panel.get("targets", []):
            sql = target.get("rawSql")
            if not sql:
                continue
            for source, destination in replacements.items():
                sql = sql.replace(source, destination)
            payload = {
                "from": "1767225600000",
                "to": "1798761600000",
                "queries": [{
                    "refId": target.get("refId", "A"),
                    "datasource": {
                        "uid": "ci-postgres",
                        "type": "grafana-postgresql-datasource",
                    },
                    "rawSql": sql,
                    "format": target.get("format", "table"),
                }],
            }
            request = Request(
                base_url.rstrip("/") + "/api/ds/query",
                data=json.dumps(payload).encode(),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            try:
                with urlopen(request, timeout=10) as response:
                    result = json.loads(response.read())
                frames = result.get("results", {}).get(target.get("refId", "A"), {}).get("frames", [])
                if not frames:
                    failures.append((panel["id"], panel["title"], "no frames"))
                checked += 1
            except Exception as error:
                body = getattr(error, "read", lambda: b"")().decode(errors="replace")
                failures.append((panel["id"], panel["title"], f"{error}: {body}"))
    print(json.dumps({"checked_queries": checked, "failures": failures}, ensure_ascii=False, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main(Path(sys.argv[1]), sys.argv[2])
