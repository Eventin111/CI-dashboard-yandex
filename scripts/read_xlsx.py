from __future__ import annotations

import json
import re
import sys
import zipfile
from datetime import datetime, timedelta
from pathlib import Path
from xml.etree import ElementTree as ET

NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
REL_NS = {"r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships"}
PKG_NS = {"p": "http://schemas.openxmlformats.org/package/2006/relationships"}


def col_index(cell_ref: str) -> int:
    letters = re.match(r"[A-Z]+", cell_ref).group(0)
    value = 0
    for letter in letters:
        value = value * 26 + ord(letter) - 64
    return value - 1


def excel_date(value: float) -> str:
    date = datetime(1899, 12, 30) + timedelta(days=value)
    if date.time() == datetime.min.time():
        return date.date().isoformat()
    return date.isoformat(sep=" ")


def main(path: Path) -> None:
    with zipfile.ZipFile(path) as archive:
        workbook = ET.fromstring(archive.read("xl/workbook.xml"))
        rels = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
        targets = {rel.attrib["Id"]: rel.attrib["Target"] for rel in rels}
        shared = []
        if "xl/sharedStrings.xml" in archive.namelist():
            root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
            for item in root.findall("m:si", NS):
                shared.append("".join(t.text or "" for t in item.iterfind(".//m:t", NS)))

        for sheet in workbook.find("m:sheets", NS):
            name = sheet.attrib["name"]
            rel_id = sheet.attrib[f"{{{REL_NS['r']}}}id"]
            target = targets[rel_id].lstrip("/")
            if not target.startswith("xl/"):
                target = "xl/" + target
            root = ET.fromstring(archive.read(target))
            rows = []
            for row in root.findall(".//m:sheetData/m:row", NS):
                values = []
                for cell in row.findall("m:c", NS):
                    idx = col_index(cell.attrib["r"])
                    while len(values) <= idx:
                        values.append(None)
                    kind = cell.attrib.get("t")
                    raw = cell.findtext("m:v", default="", namespaces=NS)
                    if kind == "s":
                        value = shared[int(raw)]
                    elif kind == "inlineStr":
                        value = "".join(t.text or "" for t in cell.iterfind(".//m:t", NS))
                    elif kind in {"str", "e"}:
                        value = raw
                    elif kind == "b":
                        value = raw == "1"
                    elif raw == "":
                        value = None
                    else:
                        number = float(raw)
                        value = int(number) if number.is_integer() else number
                    values[idx] = value
                rows.append(values)
            print(json.dumps({"sheet": name, "rows": rows}, ensure_ascii=False))


if __name__ == "__main__":
    main(Path(sys.argv[1]))
