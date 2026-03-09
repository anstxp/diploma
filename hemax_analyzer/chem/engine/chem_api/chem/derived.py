from __future__ import annotations

from typing import Optional, Dict


def egfr_ckd_epi_2021(scr_mgdl: Optional[float], age: Optional[float], sex: str) -> Optional[float]:
    if scr_mgdl is None or age is None:
        return None
    if scr_mgdl <= 0 or age <= 0:
        return None

    sex = (sex or "").lower()
    female = sex.startswith("f")
    k = 0.7 if female else 0.9
    a = -0.241 if female else -0.302

    scr_k = scr_mgdl / k
    mn = min(scr_k, 1.0) ** a
    mx = max(scr_k, 1.0) ** -1.200
    age_factor = 0.9938 ** float(age)
    sex_factor = 1.012 if female else 1.0

    egfr = 142.0 * mn * mx * age_factor * sex_factor
    return float(egfr)


def anion_gap(na: Optional[float], cl: Optional[float], hco3: Optional[float]) -> Optional[float]:
    if na is None or cl is None or hco3 is None:
        return None
    return float(na - (cl + hco3))


def non_hdl(tc: Optional[float], hdl: Optional[float]) -> Optional[float]:
    if tc is None or hdl is None:
        return None
    return float(tc - hdl)


def ldl_friedewald(tc: Optional[float], hdl: Optional[float], tg: Optional[float]) -> Optional[float]:
    if tc is None or hdl is None or tg is None:
        return None
    if tg >= 400:
        return None
    return float(tc - hdl - (tg / 5.0))


def corrected_calcium(ca: Optional[float], albumin: Optional[float]) -> Optional[float]:
    if ca is None or albumin is None:
        return None
    return float(ca + 0.8 * (4.0 - albumin))


def bun_creatinine_ratio(bun: Optional[float], cr: Optional[float]) -> Optional[float]:
    if bun is None or cr is None or cr == 0:
        return None
    return float(bun / cr)


def compute_derived(values: Dict[str, Optional[float]], sex: str, age: Optional[float]) -> Dict[str, Optional[float]]:
    na = values.get("sodium")
    cl = values.get("chloride")
    hco3 = values.get("bicarbonate") or values.get("bicarb")
    cr = values.get("creatinine")
    bun = values.get("bun")
    tc = values.get("tchol")
    hdl = values.get("hdl")
    tg = values.get("trigly")
    ca = values.get("calcium")
    alb = values.get("albumin")

    d = {}
    d["anion_gap"] = anion_gap(na, cl, hco3)
    d["egfr"] = egfr_ckd_epi_2021(cr, age, sex)
    d["non_hdl"] = non_hdl(tc, hdl)
    d["ldl_calc"] = ldl_friedewald(tc, hdl, tg)
    d["bun_cr_ratio"] = bun_creatinine_ratio(bun, cr)
    d["calcium_corrected"] = corrected_calcium(ca, alb)
    return d
