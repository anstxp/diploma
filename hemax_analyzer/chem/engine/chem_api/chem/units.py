from __future__ import annotations

import re
from typing import Optional, Tuple

_NUM = r"[-+]?(?:\d+(?:[\.,]\d+)?|[\.,]\d+)"
_UNIT_RE = re.compile(rf'^\s*({_NUM})\s*([^\d\.,].*)?\s*$')

def _norm_unit(u: Optional[str]) -> Optional[str]:
    if u is None:
        return None
    u = u.strip().lower()
    if not u:
        return None
    u = u.replace("μ", "µ")
    u = re.sub(r"\s+", "", u)
    return u

def parse_value_unit(x: object) -> Tuple[Optional[float], Optional[str]]:
    if x is None:
        return None, None
    if isinstance(x, (int, float)):
        return float(x), None
    if isinstance(x, str):
        m = _UNIT_RE.match(x)
        if not m:
            try:
            	v = float(x.strip())
            	return v, None
            except Exception:
                return None, None
        try:
            num = m.group(1).replace(",", ".")
            v = float(num)
        except Exception:
            return None, None
        u = _norm_unit(m.group(2)) if m.group(2) else None
        return v, u
    return None, None


def _is(u: Optional[str], *cands: str) -> bool:
    if u is None:
        return False
    u = _norm_unit(u)
    return u in {_norm_unit(c) for c in cands}

def to_mgdl_glucose(v: float, u: Optional[str]) -> float:
    if u is None or _is(u, "mg/dl", "mgdl"):
        return v
    if _is(u, "mmol/l", "mmoll"):
        return v * 18.0
    return v

def to_mgdl_chol(v: float, u: Optional[str]) -> float:
    if u is None or _is(u, "mg/dl", "mgdl"):
        return v
    if _is(u, "mmol/l", "mmoll"):
        return v * 38.67
    return v

def to_mgdl_trig(v: float, u: Optional[str]) -> float:
    if u is None or _is(u, "mg/dl", "mgdl"):
        return v
    if _is(u, "mmol/l", "mmoll"):
        return v * 88.57
    return v

def to_mgdl_creatinine(v: float, u: Optional[str]) -> float:
    if u is None or _is(u, "mg/dl", "mgdl"):
        return v
    if _is(u, "umol/l", "µmol/l", "µmoll", "umoll"):
        return v / 88.4
    if _is(u, "mg/l", "mgl"):
        return v / 10.0
    return v

def to_mgdl_urea(v: float, u: Optional[str]) -> float:
    if u is None or _is(u, "mg/dl", "mgdl"):
        return v
    if _is(u, "mmol/l", "mmoll"):
        return v * 6.0
    return v

def to_mgdl_bun(v: float, u: Optional[str]) -> float:
    if u is None or _is(u, "mg/dl", "mgdl"):
        return v
    if _is(u, "mmol/l", "mmoll"):
        return v * 2.801
    return v

def to_mgdl_bilirubin(v: float, u: Optional[str]) -> float:
    if u is None or _is(u, "mg/dl", "mgdl"):
        return v
    if _is(u, "umol/l", "µmol/l", "umoll", "µmoll"):
        return v / 17.1
    return v

def to_mgdl_uric(v: float, u: Optional[str]) -> float:
    if u is None or _is(u, "mg/dl", "mgdl"):
        return v
    if _is(u, "umol/l", "µmol/l", "umoll", "µmoll"):
        return v / 59.48
    return v

def to_gdl(v: float, u: Optional[str]) -> float:
    if u is None or _is(u, "g/dl", "gdl"):
        return v
    if _is(u, "g/l", "gl"):
        return v / 10.0
    return v

def to_mgl_crp(v: float, u: Optional[str]) -> float:
    if u is None or _is(u, "mg/l", "mgl"):
        return v
    if _is(u, "mg/dl", "mgdl"):
        return v * 10.0
    return v

def to_mmolL(v: float, u: Optional[str]) -> float:
    if u is None:
        return v
    if _is(u, "mmol/l", "mmoll", "meq/l", "meql"):
        return v
    return v

def to_mgdl_calcium(v: float, u: Optional[str]) -> float:
    if u is None or _is(u, "mg/dl", "mgdl"):
        return v
    if _is(u, "mmol/l", "mmoll"):
        return v * 4.0
    return v

def to_mgdl_magnesium(v: float, u: Optional[str]) -> float:
    if u is None or _is(u, "mg/dl", "mgdl"):
        return v
    if _is(u, "mmol/l", "mmoll"):
        return v * 2.4305
    return v

def to_mgdl_phosphate(v: float, u: Optional[str]) -> float:
    if u is None or _is(u, "mg/dl", "mgdl"):
        return v
    if _is(u, "mmol/l", "mmoll"):
        return v * 3.095
    return v

def to_ugdl_iron(v: float, u: Optional[str]) -> float:
    if u is None or _is(u, "ug/dl", "µg/dl", "ugdl", "µgdl"):
        return v
    if _is(u, "umol/l", "µmol/l", "umoll", "µmoll"):
        return v * 5.585
    return v

def to_pct(v: float, u: Optional[str]) -> float:
    return v
