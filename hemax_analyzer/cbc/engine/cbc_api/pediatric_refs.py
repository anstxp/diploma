from __future__ import annotations


from dataclasses import dataclass
from typing import Dict, Optional

from .knowledge import RefRange


@dataclass(frozen=True)
class PedBand:
    age_min: float
    age_max: float
    sex: Optional[str]
    labs: Dict[str, RefRange]
    abs_labs: Dict[str, RefRange]

    def matches(self, age_years: float, sex: Optional[str]) -> bool:
        if age_years < self.age_min or age_years >= self.age_max:
            return False
        if self.sex is None:
            return True
        return sex == self.sex


def _rr(low: Optional[float] = None, high: Optional[float] = None) -> RefRange:
    return RefRange(low=low, high=high)


PED_BANDS: tuple[PedBand, ...] = (
    PedBand(
        age_min=0.0,
        age_max=14.0 / 365.0,
        sex=None,
        labs={
            "hgb": _rr(14.0, 24.0),
            "rbc": _rr(3.7, 6.5),
            "hct": _rr(47.0, 75.0),
            "wbc": _rr(10.0, 26.0),
        },
        abs_labs={
            "anc": _rr(2.7, 14.4),
            "alc": _rr(2.0, 8.0),
            "amc": _rr(0.0, 2.0),
            "abc": _rr(0.0, 0.21),
            "aec": _rr(0.0, 0.81),
        },
    ),

    PedBand(
        age_min=14.0 / 365.0,
        age_max=2.0 / 12.0,
        sex=None,
        labs={
            "hgb": _rr(13.4, 19.8),
            "rbc": _rr(3.2, 5.9),
            "hct": _rr(41.0, 65.0),
            "wbc": _rr(6.0, 21.0),
        },
        abs_labs={
            "anc": _rr(1.5, 5.4),
            "alc": _rr(2.8, 9.1),
            "amc": _rr(0.1, 1.7),
            "abc": _rr(0.0, 0.21),
            "aec": _rr(0.0, 0.91),
        },
    ),

    PedBand(
        age_min=2.0 / 12.0,
        age_max=6.0 / 12.0,
        sex=None,
        labs={
            "hgb": _rr(9.4, 13.0),
            "rbc": _rr(3.1, 4.3),
            "hct": _rr(28.0, 42.0),
            "wbc": _rr(5.0, 15.0),
            "plt": _rr(150.0, 400.0),
        },
        abs_labs={
            "anc": _rr(1.0, 5.0),
            "alc": _rr(4.0, 10.0),
            "amc": _rr(0.4, 1.2),
            "abc": _rr(0.0, 0.21),
            "aec": _rr(0.0, 0.81),
        },
    ),

    PedBand(
        age_min=6.0 / 12.0,
        age_max=1.0,
        sex=None,
        labs={
            "hgb": _rr(11.1, 14.1),
            "rbc": _rr(4.1, 5.3),
            "hct": _rr(33.0, 41.0),
            "wbc": _rr(6.0, 17.5),
        },
        abs_labs={
            "anc": _rr(1.0, 8.5),
            "alc": _rr(4.0, 12.0),
            "amc": _rr(0.2, 1.0),
            "abc": _rr(0.0, 0.21),
            "aec": _rr(0.0, 0.81),
        },
    ),

    PedBand(
        age_min=1.0,
        age_max=6.0,
        sex=None,
        labs={
            "hgb": _rr(11.5, 14.0),
            "rbc": _rr(3.9, 5.3),
            "hct": _rr(34.0, 40.0),
            "wbc": _rr(5.0, 17.0),
        },
        abs_labs={
            "anc": _rr(1.0, 8.5),
            "alc": _rr(1.5, 9.5),
            "amc": _rr(0.2, 1.0),
            "abc": _rr(0.0, 0.21),
            "aec": _rr(0.0, 0.81),
        },
    ),

    PedBand(
        age_min=6.0,
        age_max=12.0,
        sex=None,
        labs={
            "hgb": _rr(11.5, 15.5),
            "rbc": _rr(4.0, 5.2),
            "hct": _rr(35.0, 40.0),
            "wbc": _rr(4.5, 14.5),
        },
        abs_labs={
            "anc": _rr(1.0, 8.0),
            "alc": _rr(1.5, 7.0),
            "amc": _rr(0.2, 1.0),
            "abc": _rr(0.0, 0.21),
            "aec": _rr(0.0, 1.01),
        },
    ),

    PedBand(
        age_min=12.0,
        age_max=18.0,
        sex="female",
        labs={
            "hgb": _rr(12.0, 16.0),
            "rbc": _rr(4.1, 5.1),
            "hct": _rr(36.0, 46.0),
            "wbc": _rr(4.5, 13.0),
        },
        abs_labs={
            "anc": _rr(1.5, 8.0),
            "alc": _rr(1.1, 4.5),
            "amc": _rr(0.2, 1.0),
            "abc": _rr(0.0, 0.21),
            "aec": _rr(0.0, 0.81),
        },
    ),
    PedBand(
        age_min=12.0,
        age_max=18.0,
        sex="male",
        labs={
            "hgb": _rr(13.0, 17.0),
            "rbc": _rr(4.5, 5.3),
            "hct": _rr(37.0, 49.0),
            "wbc": _rr(4.5, 13.0),
        },
        abs_labs={
            "anc": _rr(1.5, 8.0),
            "alc": _rr(1.1, 4.5),
            "amc": _rr(0.2, 1.0),
            "abc": _rr(0.0, 0.21),
            "aec": _rr(0.0, 0.81),
        },
    ),
)


RBC_INDICES_BY_YEAR: Dict[int, Dict[str, RefRange]] = {
    1: {"mcv": _rr(72.0, 84.0), "mch": _rr(25.0, 29.0), "mchc": _rr(32.0, 36.0)},
    2: {"mcv": _rr(71.0, 83.0), "mch": _rr(23.1, 28.2), "mchc": _rr(32.0, 35.9)},
    3: {"mcv": _rr(74.0, 87.0), "mch": _rr(24.8, 28.9), "mchc": _rr(31.3, 35.2)},
    4: {"mcv": _rr(71.0, 85.0), "mch": _rr(23.4, 29.1), "mchc": _rr(31.9, 35.6)},
    5: {"mcv": _rr(73.0, 87.0), "mch": _rr(24.0, 30.0), "mchc": _rr(32.0, 34.8)},
    6: {"mcv": _rr(74.0, 91.0), "mch": _rr(24.5, 29.6), "mchc": _rr(32.3, 36.0)},

    7: {"mcv": _rr(73.0, 87.0), "mch": _rr(23.6, 31.0), "mchc": _rr(31.9, 36.9)},
    8: {"mcv": _rr(78.0, 97.0), "mch": _rr(26.0, 29.4), "mchc": _rr(32.7, 35.8)},
    9: {"mcv": _rr(73.0, 89.0), "mch": _rr(25.3, 29.8), "mchc": _rr(32.3, 36.1)},
    10: {"mcv": _rr(76.0, 88.0), "mch": _rr(24.9, 30.2), "mchc": _rr(31.7, 35.5)},
    11: {"mcv": _rr(77.0, 95.0), "mch": _rr(25.0, 33.0), "mchc": _rr(31.0, 37.0)},
}


def get_ped_band(age_years: Optional[float], sex: Optional[str]) -> Optional[PedBand]:
    if age_years is None or age_years < 0:
        return None
    if age_years >= 18.0:
        return None
    for b in PED_BANDS:
        if b.matches(age_years, sex):
            return b
    return None


def get_pediatric_ref(code: str, age_years: Optional[float], sex: Optional[str]) -> Optional[RefRange]:
    band = get_ped_band(age_years, sex)
    if band and code in band.labs:
        return band.labs[code]

    if age_years is not None and 1.0 <= age_years < 12.0 and code in {"mcv", "mch", "mchc"}:
        yr = int(age_years)
        yr = max(1, min(11, yr))
        return RBC_INDICES_BY_YEAR.get(yr, {}).get(code)

    return None


def get_pediatric_abs_ref(code: str, age_years: Optional[float], sex: Optional[str]) -> Optional[RefRange]:
    band = get_ped_band(age_years, sex)
    if band and code in band.abs_labs:
        return band.abs_labs[code]
    return None
