from __future__ import annotations

from typing import Dict, Optional, Tuple


ADULT_REFS = {
    "sodium": (135.0, 145.0),
    "potassium": (3.5, 5.1),
    "chloride": (98.0, 107.0),
    "bicarb": (22.0, 29.0),

    "creatinine_female": (0.50, 1.10),
    "creatinine_male": (0.70, 1.30),
    "bun": (7.0, 20.0),

    "glucose": (70.0, 99.0),
    "a1c": (4.0, 5.6),

    "alt_female": (7.0, 35.0),
    "alt_male": (10.0, 40.0),
    "ast": (10.0, 40.0),
    "alp": (44.0, 147.0),
    "ggt_female": (9.0, 48.0),
    "ggt_male": (12.0, 64.0),

    "bilirubin_total": (0.1, 1.2),
    "albumin": (3.5, 5.0),
    "total_protein": (6.0, 8.3),

    "calcium": (8.6, 10.2),
    "magnesium": (1.7, 2.2),
    "phosphorus": (2.5, 4.5),
}

PEDS_REFS = {
    "creatinine": [
        ((0.0, 1.0), (0.20, 0.50)),
        ((1.0, 5.0), (0.30, 0.60)),
        ((6.0, 12.0), (0.35, 0.75)),
        ((13.0, 17.0), (0.45, 0.95)),
    ],
    "alp": [
        ((0.0, 1.0), (100.0, 550.0)),
        ((1.0, 5.0), (150.0, 420.0)),
        ((6.0, 12.0), (120.0, 500.0)),
        ((13.0, 17.0), (80.0, 390.0)),
    ],
}


def _bin_lookup(bins, age_years: float) -> Optional[Tuple[float, float]]:
    for (a0, a1), ref in bins:
        if age_years >= a0 and age_years <= a1:
            return ref
    return None


def get_ref(analyte: str, sex: str, age: float) -> Dict[str, float]:
    sex = (sex or "").lower()
    is_child = age is not None and age < 18

    if analyte == "creatinine":
        if is_child:
            ref = _bin_lookup(PEDS_REFS["creatinine"], float(age))
            if ref:
                return {"low": ref[0], "high": ref[1]}
        key = "creatinine_female" if sex.startswith("f") else "creatinine_male"
        lo, hi = ADULT_REFS[key]
        return {"low": lo, "high": hi}

    if analyte == "alt":
        key = "alt_female" if sex.startswith("f") else "alt_male"
        lo, hi = ADULT_REFS[key]
        return {"low": lo, "high": hi}

    if analyte == "ggt":
        key = "ggt_female" if sex.startswith("f") else "ggt_male"
        lo, hi = ADULT_REFS[key]
        return {"low": lo, "high": hi}

    if analyte == "alp":
        if is_child:
            ref = _bin_lookup(PEDS_REFS["alp"], float(age))
            if ref:
                return {"low": ref[0], "high": ref[1]}
        lo, hi = ADULT_REFS["alp"]
        return {"low": lo, "high": hi}

    if analyte in ADULT_REFS:
        lo, hi = ADULT_REFS[analyte]
        return {"low": lo, "high": hi}

    if analyte in ("tchol", "ldl", "trigly", "non_hdl"):
        return {"low": 0.0, "high": 1e9}
    if analyte == "hdl":
        return {"low": 0.0, "high": 1e9}

    return {"low": float("-inf"), "high": float("inf")}
