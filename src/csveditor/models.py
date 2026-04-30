from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class CsvTab:
    display_name: str
    file_path: Path | None = None
    separator: str = ","
    rows: list[list[str]] = field(default_factory=list)
    dirty: bool = False
    calculated_values: dict[tuple[int, int], str] = field(default_factory=dict)

    def set_cell(self, row: int, col: int, value: str) -> None:
        while len(self.rows) <= row:
            self.rows.append([])
        while len(self.rows[row]) <= col:
            self.rows[row].append("")
        self.rows[row][col] = value
        self.dirty = True

    def get_cell_raw(self, row: int, col: int) -> str:
        if row < 0 or col < 0:
            return ""
        if row >= len(self.rows):
            return ""
        if col >= len(self.rows[row]):
            return ""
        return self.rows[row][col]
