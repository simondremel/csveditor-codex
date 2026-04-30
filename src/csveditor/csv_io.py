from __future__ import annotations

import csv
from io import StringIO
from pathlib import Path

CANDIDATE_SEPARATORS = [",", ";", "\t", "|"]


def _split_outside_quotes(line: str, sep: str) -> int:
    in_quotes = False
    count = 0
    i = 0
    while i < len(line):
        ch = line[i]
        if ch == '"':
            if in_quotes and i + 1 < len(line) and line[i + 1] == '"':
                i += 1
            else:
                in_quotes = not in_quotes
        elif ch == sep and not in_quotes:
            count += 1
        i += 1
    return count


def detect_separator(text: str) -> str:
    lines = [ln for ln in text.splitlines() if ln.strip()][:30]
    if not lines:
        return ","

    best_sep = ","
    best_score = (-1, -1)
    for sep in CANDIDATE_SEPARATORS:
        cols = []
        for ln in lines:
            cols.append(_split_outside_quotes(ln, sep) + 1)
        consistency = 1 if len(set(cols)) == 1 else 0
        multi = sum(1 for c in cols if c > 1)
        total = sum(max(c-1,0) for c in cols)
        score = (total, consistency, multi)
        if score > best_score:
            best_score = score
            best_sep = sep
    return best_sep


def parse_csv_text(text: str, separator: str | None = None) -> tuple[list[list[str]], str]:
    sep = separator or detect_separator(text)
    reader = csv.reader(StringIO(text), delimiter=sep, quotechar='"', doublequote=True)
    rows = [list(row) for row in reader]
    return rows, sep


def read_csv(path: Path) -> tuple[list[list[str]], str]:
    text = path.read_text(encoding="utf-8")
    return parse_csv_text(text)


def write_csv_text(rows: list[list[str]], separator: str) -> str:
    out = StringIO()
    writer = csv.writer(
        out,
        delimiter=separator,
        quotechar='"',
        lineterminator="\n",
        quoting=csv.QUOTE_ALL,
        doublequote=True,
    )
    for row in rows:
        writer.writerow(row)
    return out.getvalue()


def write_csv(path: Path, rows: list[list[str]], separator: str) -> None:
    path.write_text(write_csv_text(rows, separator), encoding="utf-8")
