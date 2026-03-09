from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional, Tuple, Any


@dataclass
class Parsed:
    value: Optional[float]
    unit: Optional[str]
    raw: Any


_NUM_RE = re.compile(r"([-+]?\d+(?:\.\d+)?)")
_UNIT_RE = re.compile(r"[A-Za-zµμ/%^0-9·\-\s]+")


def _normalize_unit(u: str) -> str:
    u = u.strip()
    u = u.replace("μ", "µ")
    u = u.replace("umol", "µmol")
    u = u.replace("uL", "µL")
    u = u.replace("per", "/")
    u = re.sub(r"\s+", " ", u)
    return u


def parse_number_and_unit(x: Any) -> Parsed:
    if x is None:
        return Parsed(None, None, x)
    if isinstance(x, (int, float)):
        return Parsed(float(x), None, x)
    s = str(x).strip()
    if not s:
        return Parsed(None, None, x)

    m = _NUM_RE.search(s)
    if not m:
        return Parsed(None, None, x)
    val = float(m.group(1))

    rest = s[m.end():].strip()
    unit = _normalize_unit(rest) if rest else None
    return Parsed(val, unit, x)


def _to_mgdl_from_mmol_l(val: float, factor: float) -> float:
    return val * factor


def _convert(val: float, unit: Optional[str], target: str, analyte: str) -> Tuple[float, str]:
    if unit is None:
        return val, target

    u = unit.lower().replace(" ", "")
    t = target.lower().replace(" ", "")

    u = u.replace("meq/l", "mmol/l")

    u = u.replace("mgdl", "mg/dl").replace("mmoll", "mmol/l").replace("umol/l", "µmol/l")

    if u == t:
        return val, target

    if analyte == "glucose":
        if u in ("mmol/l",):
            return _to_mgdl_from_mmol_l(val, 18.0182), "mg/dL"
        if u in ("mg/dl",):
            return val, "mg/dL"

    if analyte == "creatinine":
        if u in ("µmol/l",):
            return val / 88.4, "mg/dL"
        if u in ("mg/dl",):
            return val, "mg/dL"

    if analyte == "bun":
        if u in ("mmol/l",) and "urea" in (analyte,):
            return val * 2.801, "mg/dL"
        if u in ("mg/dl",):
            return val, "mg/dL"
        if u in ("mg/dl",) and analyte == "bun":
            return val, "mg/dL"

    if analyte == "bilirubin_total":
        if u in ("µmol/l",):
            return val / 17.1, "mg/dL"
        if u in ("mg/dl",):
            return val, "mg/dL"

    if analyte == "albumin":
        if u in ("g/l",):
            return val / 10.0, "g/dL"
        if u in ("g/dl",):
            return val, "g/dL"

    if analyte == "total_protein":
        if u in ("g/l",):
            return val / 10.0, "g/dL"
        if u in ("g/dl",):
            return val, "g/dL"

    if analyte in ("tchol", "hdl", "ldl", "non_hdl"):
        if u in ("mmol/l",):
            return val * 38.67, "mg/dL"
        if u in ("mg/dl",):
            return val, "mg/dL"

    if analyte in ("trigly",):
        if u in ("mmol/l",):
            return val * 88.57, "mg/dL"
        if u in ("mg/dl",):
            return val, "mg/dL"

    if analyte == "calcium":
        if u in ("mmol/l",):
            return val * 4.008, "mg/dL"
        if u in ("mg/dl",):
            return val, "mg/dL"

    if analyte == "magnesium":
        if u in ("mmol/l",):
            return val * 2.43, "mg/dL"
        if u in ("mg/dl",):
            return val, "mg/dL"

    if analyte == "phosphorus":
        if u in ("mmol/l",):
            return val * 3.097, "mg/dL"
        if u in ("mg/dl",):
            return val, "mg/dL"

    if analyte in ("sodium", "potassium", "chloride", "bicarb"):
        if u in ("mmol/l",):
            return val, "mmol/L"

    if analyte in ("alt", "ast", "alp", "ggt"):
        if u in ("u/l", "iu/l"):
            return val, "U/L"

    if analyte == "a1c":
        if u in ("%", "pct"):
            return val, "%"
        return val, "%"

    return val, target


def parse_analyte(x: Any, analyte: str) -> Tuple[Optional[float], Optional[str]]:
    p = parse_number_and_unit(x)
    if p.value is None:
        return None, None

    target = {
        "sodium": "mmol/L",
        "potassium": "mmol/L",
        "chloride": "mmol/L",
        "bicarb": "mmol/L",
        "glucose": "mg/dL",
        "a1c": "%",
        "creatinine": "mg/dL",
        "bun": "mg/dL",
        "alt": "U/L",
        "ast": "U/L",
        "alp": "U/L",
        "ggt": "U/L",
        "bilirubin_total": "mg/dL",
        "albumin": "g/dL",
        "total_protein": "g/dL",
        "calcium": "mg/dL",
        "magnesium": "mg/dL",
        "phosphorus": "mg/dL",
        "tchol": "mg/dL",
        "hdl": "mg/dL",
        "ldl": "mg/dL",
        "trigly": "mg/dL",
        "non_hdl": "mg/dL",
    }.get(analyte, None)

    if target is None:
        return p.value, p.unit

    v, u = _convert(p.value, p.unit, target, analyte)
    return float(v) if v is not None else None, u
