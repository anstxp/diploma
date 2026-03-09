from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Dict, Any

@dataclass(frozen=True)
class RefRange:
    low: Optional[float] = None
    high: Optional[float] = None

@dataclass(frozen=True)
class LabDef:
    code: str
    name: str
    unit: str
    ref_male: RefRange = RefRange()
    ref_female: RefRange = RefRange()
    ref_any: RefRange = RefRange()
    what: str = ""
    tips: tuple[str, ...] = ()
    group: str = "other"

    def ref_for(self, sex: Optional[str]) -> RefRange:
        sx = (sex or "").strip().lower()
        if self.ref_any.low is not None or self.ref_any.high is not None:
            return self.ref_any
        if sx in ("male","m"):
            return self.ref_male
        if sx in ("female","f"):
            return self.ref_female
        return self.ref_male if (self.ref_male.low is not None or self.ref_male.high is not None) else self.ref_female
