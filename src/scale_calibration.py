from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Mapping


SCALE_COLUMNS = (
    "scale_image", "scale_x1", "scale_y1", "scale_x2", "scale_y2",
    "scale_length", "scale_unit", "scale_pixels", "scale_units_per_pixel",
    "coordinate_space", "coordinate_unit",
)


@dataclass(frozen=True)
class ScaleCalibration:
    image: str
    start: tuple[float, float]
    end: tuple[float, float]
    length: float
    unit: str
    export_real: bool = False

    def __post_init__(self) -> None:
        if not self.image.strip() or not self.unit.strip():
            raise ValueError("A reference image and a unit are required.")
        if not math.isfinite(self.length) or self.length <= 0:
            raise ValueError("The real length must be finite and greater than zero.")
        if any(not math.isfinite(value) or value < 0 for value in (*self.start, *self.end)):
            raise ValueError("Scale coordinates must be finite and non-negative.")
        if not math.isfinite(self.pixels) or self.pixels == 0:
            raise ValueError("The scale endpoints must be distinct.")
        if not math.isfinite(self.length / self.pixels) or self.length / self.pixels == 0:
            raise ValueError("The scale conversion factor is out of range.")

    @property
    def pixels(self) -> float:
        return math.hypot(self.end[0] - self.start[0], self.end[1] - self.start[1])

    def to_csv(self) -> dict[str, str]:
        values = (
            self.image, *self.start, *self.end, self.length, self.unit,
            self.pixels, self.length / self.pixels,
            "real" if self.export_real else "pixel", self.unit if self.export_real else "px",
        )
        return dict(zip(SCALE_COLUMNS, map(str, values)))

    @classmethod
    def from_csv(cls, row: Mapping[str, str | None]) -> ScaleCalibration | None:
        if not any(row.get(column) for column in SCALE_COLUMNS):
            return None
        required = SCALE_COLUMNS[:7]
        if any(not row.get(column) for column in required):
            raise ValueError("Incomplete scale data in annotations.csv.")
        space = row.get("coordinate_space") or "pixel"
        if space not in {"pixel", "real"}:
            raise ValueError("Invalid coordinate space in annotations.csv.")
        expected_unit = row["scale_unit"] if space == "real" else "px"
        if row.get("coordinate_unit") and row["coordinate_unit"] != expected_unit:
            raise ValueError("Inconsistent coordinate unit in annotations.csv.")
        return cls(
            image=str(row["scale_image"]),
            start=(float(str(row["scale_x1"])), float(str(row["scale_y1"]))),
            end=(float(str(row["scale_x2"])), float(str(row["scale_y2"]))),
            length=float(str(row["scale_length"])),
            unit=str(row["scale_unit"]),
            export_real=space == "real",
        )
