
from __future__ import annotations


CBC_VARS = {
    "LBXWBCSI": {"name": "WBC (лейкоцити)", "unit": "10^3/µL"},
    "LBXNEPCT": {"name": "Neutrophils % (нейтрофіли, %)", "unit": "%"},
    "LBXLYPCT": {"name": "Lymphocytes % (лімфоцити, %)", "unit": "%"},
    "LBXMOPCT": {"name": "Monocytes % (моноцити, %)", "unit": "%"},
    "LBXEOPCT": {"name": "Eosinophils % (еозинофіли, %)", "unit": "%"},
    "LBXBAPCT": {"name": "Basophils % (базофіли, %)", "unit": "%"},
    "LBDNENO": {"name": "Neutrophils abs (ANC)", "unit": "10^3/µL"},
    "LBDLYMNO": {"name": "Lymphocytes abs (ALC)", "unit": "10^3/µL"},
    "LBDMONO": {"name": "Monocytes abs", "unit": "10^3/µL"},
    "LBDEONO": {"name": "Eosinophils abs", "unit": "10^3/µL"},
    "LBDBANO": {"name": "Basophils abs", "unit": "10^3/µL"},

    "LBXRBCSI": {"name": "RBC (еритроцити)", "unit": "10^6/µL"},
    "LBXHGB": {"name": "Hemoglobin (Hb)", "unit": "g/dL"},
    "LBXHCT": {"name": "Hematocrit (Hct)", "unit": "%"},
    "LBXMCVSI": {"name": "MCV", "unit": "fL"},
    "LBXMCHSI": {"name": "MCH", "unit": "pg"},
    "LBXMC": {"name": "MCHC", "unit": "g/dL"},
    "LBXRDW": {"name": "RDW", "unit": "%"},
    "LBXPLTSI": {"name": "Platelets (тромбоцити)", "unit": "10^3/µL"},
    "LBXMPSI": {"name": "MPV (середній обʼєм тромбоцитів)", "unit": "fL"},
}

CBC_CORE = [
    "LBXWBCSI",
    "LBXNEPCT", "LBXLYPCT", "LBXMOPCT", "LBXEOPCT", "LBXBAPCT",
    "LBXRBCSI", "LBXHGB", "LBXHCT", "LBXMCVSI", "LBXMCHSI", "LBXMC", "LBXRDW",
    "LBXPLTSI", "LBXMPSI",
]

DIFF_ABS = {
    "LBDNENO": ("LBXWBCSI", "LBXNEPCT"),
    "LBDLYMNO": ("LBXWBCSI", "LBXLYPCT"),
    "LBDMONO": ("LBXWBCSI", "LBXMOPCT"),
    "LBDEONO": ("LBXWBCSI", "LBXEOPCT"),
    "LBDBANO": ("LBXWBCSI", "LBXBAPCT"),
}
