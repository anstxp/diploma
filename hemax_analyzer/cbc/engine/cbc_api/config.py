from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any, Dict, Optional, Tuple


@dataclass(frozen=True)
class SeverityBand:

    mild: float
    moderate: float
    severe: float


@dataclass
class CBCConfig:

    wbc_high: SeverityBand = SeverityBand(mild=11.1, moderate=15.0, severe=25.0)
    wbc_low: SeverityBand = SeverityBand(mild=3.5, moderate=2.0, severe=1.0)

    anc_high: SeverityBand = SeverityBand(mild=7.6, moderate=12.0, severe=20.0)
    anc_low: SeverityBand = SeverityBand(mild=1.5, moderate=1.0, severe=0.5)

    plt_high: SeverityBand = SeverityBand(mild=450.0, moderate=600.0, severe=1000.0)
    plt_low: SeverityBand = SeverityBand(mild=150.0, moderate=100.0, severe=50.0)

    esr_high: SeverityBand = SeverityBand(mild=20.0, moderate=50.0, severe=100.0)

    hgb_low_female: SeverityBand = SeverityBand(mild=12.0, moderate=9.0, severe=7.0)
    hgb_low_male: SeverityBand = SeverityBand(mild=13.0, moderate=10.0, severe=7.5)

    mcv_micro: float = 80.0
    mcv_macro: float = 100.0
    nlr_high_cutoff: float = 6.0

    lab_order: Tuple[str, ...] = (
        "wbc",
        "neut_pct", "lymph_pct", "mono_pct", "eos_pct", "baso_pct",
        "anc", "alc", "amc", "aec", "abc",
        "rbc", "hgb", "hct", "mcv", "mch", "mchc", "rdw",
        "plt", "mpv",
    )

    signal_priority: Dict[str, int] = field(default_factory=lambda: {
        "pancytopenia_pattern": 100,
        "neutropenia": 95,
        "thrombocytopenia": 90,
        "leukopenia": 80,

        "microcytic_anemia_pattern": 70,
        "macrocytic_anemia_pattern": 70,
        "normocytic_anemia_pattern": 70,
        "iron_deficiency_likely_pattern": 65,
        "plt_high_microcytosis_combo": 60,
        "thal_trait_like_pattern": 55,

        "anemia_possible": 50,
        "leukocytosis": 45,
        "neutrophilia": 45,
        "lymphocytosis": 40,
        "eosinophilia": 35,
        "monocytosis": 30,
        "basophilia": 30,
        "thrombocytosis": 25,

        "nlr_high": 10,

        "missing_core_cbc": -100,
    })


def _parse_severity_band(obj: Any, default: SeverityBand) -> SeverityBand:
    if not isinstance(obj, dict):
        return default
    def _get(name: str, fallback: float) -> float:
        try:
            v = obj.get(name, fallback)
            return float(v)
        except Exception:
            return fallback
    return SeverityBand(
        mild=_get("mild", default.mild),
        moderate=_get("moderate", default.moderate),
        severe=_get("severe", default.severe),
    )


def load_config(payload: Optional[Dict[str, Any]]) -> CBCConfig:
    cfg = CBCConfig()
    if not payload or not isinstance(payload, dict):
        cfg = _maybe_apply_empirical(cfg)
        return cfg

    raw = payload.get("config")
    if not isinstance(raw, dict):
        cfg = _maybe_apply_empirical(cfg)
        return cfg

    th = raw.get("severity_thresholds")
    if isinstance(th, dict):
        cfg = CBCConfig(
            wbc_high=_parse_severity_band(th.get("wbc_high"), cfg.wbc_high),
            wbc_low=_parse_severity_band(th.get("wbc_low"), cfg.wbc_low),
            anc_high=_parse_severity_band(th.get("anc_high"), cfg.anc_high),
            anc_low=_parse_severity_band(th.get("anc_low"), cfg.anc_low),
            plt_high=_parse_severity_band(th.get("plt_high"), cfg.plt_high),
            plt_low=_parse_severity_band(th.get("plt_low"), cfg.plt_low),
            hgb_low_female=_parse_severity_band(th.get("hgb_low_female"), cfg.hgb_low_female),
            hgb_low_male=_parse_severity_band(th.get("hgb_low_male"), cfg.hgb_low_male),
            mcv_micro=float(th.get("mcv_micro", cfg.mcv_micro)),
            mcv_macro=float(th.get("mcv_macro", cfg.mcv_macro)),
            nlr_high_cutoff=float(th.get("nlr_high_cutoff", cfg.nlr_high_cutoff)),
            lab_order=cfg.lab_order,
            signal_priority=cfg.signal_priority,
        )

    lo = raw.get("lab_order")
    if isinstance(lo, list) and all(isinstance(x, str) for x in lo):
        cfg.lab_order = tuple(lo)  # type: ignore[misc]

    sp = raw.get("signal_priority")
    if isinstance(sp, dict):
        merged = dict(cfg.signal_priority)
        for k, v in sp.items():
            try:
                merged[str(k)] = int(v)
            except Exception:
                continue
        cfg.signal_priority = merged  # type: ignore[assignment]

    cfg = _maybe_apply_empirical(cfg)

    return cfg



def _maybe_apply_empirical(cfg: CBCConfig) -> CBCConfig:
    try:
        from .empirical_refs_loader import EmpiricalConfig  # type: ignore
    except Exception:
        return cfg
    ec = EmpiricalConfig.try_load_from_env()
    if ec is None:
        return cfg

    for band_attr in ("wbc_high", "wbc_low", "anc_high", "anc_low"):
        band = ec.get_severity(band_attr)
        if band is not None:
            cfg = replace(cfg, **{band_attr: band})

    plt_high_f = ec.get_severity("plt_high", sex="female")
    plt_high_m = ec.get_severity("plt_high", sex="male")
    if plt_high_f and plt_high_m:
        cfg = replace(cfg, plt_high=SeverityBand(
            mild=min(plt_high_f.mild, plt_high_m.mild),
            moderate=min(plt_high_f.moderate, plt_high_m.moderate),
            severe=min(plt_high_f.severe, plt_high_m.severe),
        ))
    plt_low_f = ec.get_severity("plt_low", sex="female")
    plt_low_m = ec.get_severity("plt_low", sex="male")
    if plt_low_f and plt_low_m:
        cfg = replace(cfg, plt_low=SeverityBand(
            mild=max(plt_low_f.mild, plt_low_m.mild),
            moderate=max(plt_low_f.moderate, plt_low_m.moderate),
            severe=max(plt_low_f.severe, plt_low_m.severe),
        ))

    return cfg
