from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Tuple

@dataclass(frozen=True)
class SeverityBand:
    mild: float
    moderate: float
    severe: float

@dataclass
class ChemConfig:
    glucose_high: SeverityBand = SeverityBand(mild=110, moderate=126, severe=250)
    glucose_low: SeverityBand = SeverityBand(mild=70, moderate=54, severe=40)

    potassium_high: SeverityBand = SeverityBand(mild=5.5, moderate=6.0, severe=6.5)
    potassium_low: SeverityBand = SeverityBand(mild=3.4, moderate=3.0, severe=2.5)

    sodium_high: SeverityBand = SeverityBand(mild=146, moderate=150, severe=160)
    sodium_low: SeverityBand = SeverityBand(mild=134, moderate=130, severe=120)

    trigly_high: SeverityBand = SeverityBand(mild=150, moderate=200, severe=500)

    lab_order: Tuple[str, ...] = (
        "glucose","a1c",
        "creatinine","egfr","urea","bun",
        "sodium","potassium","chloride","bicarbonate","anion_gap",
        "calcium","calcium_corrected","magnesium","phosphate",
        "alt","ast","alp","ggt","bilirubin_total","bilirubin_direct","ast_alt_ratio",
        "albumin","total_protein","globulin","ag_ratio",
        "tchol","ldl","hdl","trigly","non_hdl","tc_hdl_ratio","tg_hdl_ratio",
        "crp",
        "iron","ferritin","tibc","tsat",
        "uric_acid",
        "amylase","lipase","ck","ldh",
        "vitd_25oh",
    )

    signal_priority: Dict[str, int] = field(default_factory=lambda: {
        "hyperkalemia": 120,
        "hypokalemia": 120,
        "hyponatremia": 110,
        "hypernatremia": 110,
        "severe_hypoglycemia": 110,

        "egfr_low": 100,
        "creatinine_high": 95,
        "bilirubin_high": 90,
        "transaminitis": 80,

        "glucose_diabetes_range": 70,
        "a1c_diabetes_range": 70,
        "glucose_ifg_range": 60,
        "a1c_prediabetes_range": 60,
        "hypertriglyceridemia": 55,
        "atherogenic_dyslipidemia_pattern": 50,
        "low_hdl": 45,
        "tchol_high": 40,
        "non_hdl_high": 45,
        "tg_hdl_ratio_high": 30,
        "crp_high": 40,


        "iron_deficiency_likely": 45,
        "low_tsat": 44,
        "high_tsat": 20,
        "ferritin_high_possible_inflammation": 35,

        "missing_core_chem": -100,

        "uric_acid_high": 35,
        "vitd_deficiency": 40,
        "vitd_insufficiency": 20,
        "vitd_high": 10,
        "bicarbonate_low": 85,
        "bicarbonate_high": 50,
        "chloride_low": 25,
        "chloride_high": 25,
    })
