from __future__ import annotations

import re
from typing import Optional


_NUM_RE = re.compile(r"^[-+]?(\d+(?:[.,]\d+)?)")


def parse_lab_value(value) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if not isinstance(value, str):
        return None
    s = value.strip()
    m = _NUM_RE.match(s)
    if not m:
        return None
    try:
        return float(m.group(1).replace(",", "."))
    except ValueError:
        return None


def normalize_lab_to_us_units(value, lab_name: str) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if not isinstance(value, str):
        return None

    s = value.strip().lower()
    num = parse_lab_value(s)
    if num is None:
        return None

    has_mmol = "mmol" in s
    has_umol = "µmol" in s or "umol" in s or "мкмоль" in s
    has_mgdl = "mg/dl" in s or "мг/дл" in s
    has_gl   = (" g/l" in s or s.endswith("g/l")
                or " г/л" in s or s.endswith("г/л"))

    name = lab_name.lower()

    if name in ("glucose", "glucose_fasting", "fasting_glucose"):
        if has_mmol:
            return round(num * 18.0182, 1)
        if has_mgdl:
            return num
        return round(num * 18.0182, 1) if num <= 25 else num

    if name in ("tchol", "tchol_mgdl", "total_cholesterol", "hdl", "hdl_mgdl",
                "ldl", "ldl_mgdl"):
        if has_mmol:
            return round(num * 38.67, 1)
        if has_mgdl:
            return num
        return round(num * 38.67, 1) if num <= 15 else num
    if name in ("trigly", "trigly_mgdl", "triglycerides"):
        if has_mmol:
            return round(num * 88.57, 1)
        if has_mgdl:
            return num
        return round(num * 88.57, 1) if num <= 15 else num

    if name in ("non_hdl_mgdl", "non_hdl"):
        if has_mmol:
            return round(num * 38.67, 1)
        return num

    if name in ("creatinine", "creatinine_mgdl"):
        if has_umol:
            return round(num / 88.4017, 2)
        if has_mgdl:
            return num
        return num if num <= 10 else round(num / 88.4017, 2)

    if name in ("urea",):
        if has_mmol:
            return round(num * 6.0, 1)
        return num
    if name in ("bun", "bun_mgdl"):
        if has_mmol:
            return round(num * 2.8, 1)
        return num

    if name in ("bilirubin", "bilirubin_total"):
        if has_umol:
            return round(num / 17.1, 2)
        return num

    if name in ("uric_acid", "uric_acid_mgdl"):
        if has_umol:
            return round(num / 59.48, 2)
        return num

    if name in ("hb_gdl", "hgb", "hemoglobin", "hb"):
        if has_gl:
            return round(num / 10.0, 1)
        return round(num / 10.0, 1) if num >= 40 else num

    if name in ("iron_chem_ugdl", "iron", "serum_iron"):
        if has_umol:
            return round(num * 5.587, 1)
        return num

    if name in ("albumin_gdl", "albumin"):
        if has_gl:
            return round(num / 10.0, 1)
        return round(num / 10.0, 1) if num >= 25 else num

    if name in ("globulin_gdl", "globulin"):
        if has_gl:
            return round(num / 10.0, 1)
        return round(num / 10.0, 1) if num >= 15 else num

    if name in ("protein_total_gdl", "total_protein", "protein_total"):
        if has_gl:
            return round(num / 10.0, 1)
        return round(num / 10.0, 1) if num >= 40 else num

    if name in ("calcium_mgdl", "calcium"):
        if has_mmol:
            return round(num * 4.008, 1)
        return num
    if name in ("phosphorus_mgdl", "phosphorus", "phosphate"):
        if has_mmol:
            return round(num * 3.097, 1)
        return num

    if name in ("hba1c", "a1c", "hba1c_pct"):
        return num

    if name in ("crp", "hs_crp"):
        return num

    if name in ("ferritin", "ferritin_ngml"):
        return num

    if name in ("vit_d", "vit_d_total", "vitamin_d", "vitd_25oh"):
        if "nmol" in s:
            return round(num / 2.496, 1)
        return num

    if name in ("sodium", "sodium_mmoll", "potassium", "potassium_mmoll",
                "chloride", "chloride_mmoll", "bicarbonate", "bicarbonate_mmoll"):
        return num

    return num
