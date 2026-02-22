from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


try:
    from .knowledge import RefRange       # type: ignore
    from .config import SeverityBand      # type: ignore
except ImportError:
    from dataclasses import dataclass as _dc
    @_dc(frozen=True)
    class RefRange:                       # type: ignore
        low: Optional[float] = None
        high: Optional[float] = None
    @_dc(frozen=True)
    class SeverityBand:                   # type: ignore
        mild: float = 0.0
        moderate: float = 0.0
        severe: float = 0.0


ADULT_AGE_THRESHOLD: float = 18.0


@dataclass
class EmpiricalConfig:
    raw: dict
    source_path: Optional[Path] = None

    @classmethod
    def load(cls, path: os.PathLike | str) -> "EmpiricalConfig":
        p = Path(path)
        with open(p) as f:
            raw = json.load(f)
        if "reference_intervals" not in raw or "severity_bands" not in raw:
            raise ValueError(
                f"{p} is not a valid engine config "
                "(missing reference_intervals / severity_bands)"
            )
        return cls(raw=raw, source_path=p)

    @classmethod
    def try_load_from_env(cls) -> Optional["EmpiricalConfig"]:
        p = os.environ.get("CBC_ENGINE_CONFIG")
        if not p:
            return None
        if not os.path.isfile(p):
            return None
        try:
            return cls.load(p)
        except Exception:
            return None

    def get_ref(
        self,
        engine_code: str,
        sex: Optional[str],
        age_years: Optional[float],
    ) -> Optional[RefRange]:
        if age_years is not None and age_years < ADULT_AGE_THRESHOLD:
            return None

        entry = self.raw["reference_intervals"].get(engine_code)
        if entry is None:
            return None

        if entry.get("partition_by") == "none":
            lo, hi = entry["any"]
            return RefRange(low=float(lo), high=float(hi))

        if entry.get("partition_by") == "sex":
            if sex is None:
                return None
            key = self._norm_sex(sex)
            if key is None:
                return None
            if key not in entry:
                return None
            lo, hi = entry[key]
            return RefRange(low=float(lo), high=float(hi))

        return None

    def get_severity(
        self,
        band_name: str,
        sex: Optional[str] = None,
    ) -> Optional[SeverityBand]:
        entry = self.raw["severity_bands"].get(band_name)
        if entry is None:
            return None

        if entry.get("partition_by") == "none":
            return SeverityBand(
                mild     = float(entry["mild"]),
                moderate = float(entry["moderate"]),
                severe   = float(entry["severe"]),
            )

        if entry.get("partition_by") == "sex":
            if sex is None:
                return None
            key = self._norm_sex(sex)
            if key is None or key not in entry:
                return None
            sub = entry[key]
            return SeverityBand(
                mild     = float(sub["mild"]),
                moderate = float(sub["moderate"]),
                severe   = float(sub["severe"]),
            )

        return None

    @property
    def metadata(self) -> dict:
        return self.raw.get("metadata", {})

    def has_biomarker(self, engine_code: str) -> bool:
        return engine_code in self.raw["reference_intervals"]

    def has_band(self, band_name: str) -> bool:
        return band_name in self.raw["severity_bands"]

    def biomarker_codes(self) -> list[str]:
        return sorted(self.raw["reference_intervals"].keys())

    def band_names(self) -> list[str]:
        return sorted(self.raw["severity_bands"].keys())

    @staticmethod
    def _norm_sex(sex: object) -> Optional[str]:
        if sex is None:
            return None
        s = str(sex).strip().lower()
        if s in {"f", "female", "woman", "ж", "жінка", "2"}:
            return "female"
        if s in {"m", "male", "man", "ч", "чоловік", "1"}:
            return "male"
        return None
