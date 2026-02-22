from __future__ import annotations

import re
from typing import Optional, Tuple

_NUM = r"[-+]?(?:\d+(?:\.\d+)?|\.\d+)"
_UNIT_RE = re.compile(rf'^\s*({_NUM})\s*(.+)?\s*$')

def _norm_unit(u: Optional[str]) -> Optional[str]:
    if u is None:
        return None
    u = u.strip().lower()
    if not u:
        return None
    u = u.replace("μ", "µ")
    u = re.sub(r"\s+", "", u)
    u = u.replace("per", "/")
    u = u.replace("×", "x")
    u = u.replace("10^3", "k")
    u = u.replace("10^6", "m")
    u = u.replace("10^9", "g")
    u = u.replace("cells", "")
    return u

def parse_value_unit(x: object) -> Tuple[Optional[float], Optional[str]]:
    if x is None:
        return None, None
    if isinstance(x, (int, float)):
        if isinstance(x, float) and (x != x):
            return None, None
        return float(x), None
    s = str(x).strip()
    if not s:
        return None, None
    m = _UNIT_RE.match(s)
    if not m:
        try:
            return float(s), None
        except Exception:
            return None, None
    val = float(m.group(1))
    unit = m.group(2)
    return val, (unit.strip() if unit else None)


def to_kul(value: float, unit: Optional[str]) -> float:
    u = _norm_unit(unit)
    if u is None:
        return float(value)
    if u in {"k/ul","k/µl","xk/ul","xk/µl","10^3/ul","10^3/µl","x10^3/ul","x10^3/µl","k/uL".lower()}:
        return float(value)
    if u in {"10^9/l","x10^9/l","g/l"}:
        return float(value)
    if u in {"/ul","/µl","ul^-1","µl^-1"}:
        return float(value) / 1000.0
    if u in {"/l","l^-1"}:
        return float(value) / 1e9
    return float(value)

def to_mul(value: float, unit: Optional[str]) -> float:
    u = _norm_unit(unit)
    if u is None:
        return float(value)
    if u in {"m/ul","m/µl","10^6/ul","10^6/µl","x10^6/ul","x10^6/µl","10^6/µl".lower()}:
        return float(value)
    if u in {"10^12/l","x10^12/l"}:
        return float(value)
    if u in {"/ul","/µl"}:
        return float(value) / 1e6
    if u in {"/l"}:
        return float(value) / 1e12
    return float(value)

def to_gdl_hb(value: float, unit: Optional[str]) -> float:
    u = _norm_unit(unit)
    if u is None or u in {"g/dl","gdl"}:
        return float(value)
    if u in {"g/l","g/liter","g/litre"}:
        return float(value) / 10.0
    return float(value)

def to_pct(value: float, unit: Optional[str]) -> float:
    u = _norm_unit(unit)
    if u is None:
        return float(value)
    if u in {"%","pct"}:
        return float(value)
    return float(value)

def to_fl(value: float, unit: Optional[str]) -> float:
    u = _norm_unit(unit)
    if u is None or u in {"fl"}:
        return float(value)
    return float(value)

def to_pg(value: float, unit: Optional[str]) -> float:
    u = _norm_unit(unit)
    if u is None or u in {"pg"}:
        return float(value)
    return float(value)

def to_gdl_mchc(value: float, unit: Optional[str]) -> float:
    u = _norm_unit(unit)
    if u is None or u in {"g/dl","gdl"}:
        return float(value)
    if u in {"g/l"}:
        return float(value)/10.0
    return float(value)

def smart_round(x: Optional[float], nd: int = 3) -> Optional[float]:
    if x is None:
        return None
    try:
        return round(float(x), nd)
    except Exception:
        return None
