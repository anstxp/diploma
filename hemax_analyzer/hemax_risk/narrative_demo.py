from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from risk_api.narrative import build_narrative
from risk_api.risk.inference import RiskPredictor


PATIENTS = [
    ("Здорова молода жінка",
     "F28, всі показники в нормі",
     {"sex": "female", "age": 28, "bmi": 22, "waist_cm": 72,
      "sbp": 115, "dbp": 72, "pulse": 70,
      "labs": {"hgb": 13.2, "wbc": 6.1, "plt": 240, "mcv": 90,
               "glucose": 88, "hba1c": 5.2, "creatinine": 0.8,
               "alt": 18, "ast": 20, "tchol": 175, "hdl": 65, "trigly": 75,
               "crp": 0.8, "sodium": 140, "potassium": 4.2}}),
    ("Переддіабет + ожиріння",
     "M55, BMI 32, HbA1c 6.3, високий BP",
     {"sex": "male", "age": 55, "bmi": 32, "waist_cm": 108,
      "sbp": 142, "dbp": 92, "pulse": 78,
      "labs": {"hgb": 14.5, "wbc": 7.5, "plt": 280, "mcv": 88,
               "glucose": 118, "hba1c": 6.3, "creatinine": 1.0,
               "alt": 38, "ast": 32, "tchol": 215, "hdl": 38, "trigly": 195,
               "crp": 4.1}}),
    ("Літня жінка з відомою гіпертонією",
     "F70, AT 152/88, холестерин 240",
     {"sex": "female", "age": 70, "bmi": 28, "waist_cm": 98,
      "sbp": 152, "dbp": 88, "pulse": 75,
      "labs": {"hgb": 12.8, "wbc": 7.0, "plt": 260, "mcv": 92,
               "glucose": 102, "hba1c": 5.9, "creatinine": 1.3,
               "alt": 28, "ast": 30, "tchol": 240, "hdl": 48, "trigly": 165,
               "crp": 3.2}}),
    ("Молодий чоловік-курець",
     "M40, AT 132/85, hs-CRP 3.5",
     {"sex": "male", "age": 40, "bmi": 26, "waist_cm": 92,
      "sbp": 132, "dbp": 85, "pulse": 76,
      "labs": {"hgb": 15.0, "wbc": 7.8, "plt": 270, "mcv": 89,
               "glucose": 95, "hba1c": 5.4, "creatinine": 0.95,
               "alt": 28, "ast": 26, "tchol": 210, "hdl": 42, "trigly": 158,
               "crp": 3.5}}),
    ("Метаболічно здоровий 50",
     "M50, нормальні всі показники",
     {"sex": "male", "age": 50, "bmi": 23, "waist_cm": 84,
      "sbp": 122, "dbp": 78, "pulse": 68,
      "labs": {"hgb": 14.6, "wbc": 5.8, "plt": 230, "mcv": 91,
               "glucose": 92, "hba1c": 5.3, "creatinine": 0.9,
               "alt": 22, "ast": 24, "tchol": 180, "hdl": 58, "trigly": 95,
               "crp": 0.9}}),
    ("Недіагностований діабет",
     "M48, HbA1c 7.5, glucose 158",
     {"sex": "male", "age": 48, "bmi": 30, "waist_cm": 102,
      "sbp": 138, "dbp": 88,
      "labs": {"glucose": 158, "hba1c": 7.5, "creatinine": 1.0,
               "tchol": 220, "hdl": 35, "trigly": 240, "crp": 3.8,
               "hgb": 14.2, "plt": 250, "alt": 32}}),
    ("Кардіоваскулярний пацієнт",
     "M65, попередній інфаркт у анамнезі профілю",
     {"sex": "male", "age": 65, "bmi": 27, "waist_cm": 98,
      "sbp": 145, "dbp": 90,
      "labs": {"glucose": 105, "hba1c": 6.0, "creatinine": 1.4,
               "tchol": 230, "hdl": 38, "trigly": 180, "crp": 2.8,
               "hgb": 13.5, "plt": 220, "alt": 30}}),
    ("Молодий професіонал перевантажений",
     "M35, працює багато, помірний BMI, sleep deprivation",
     {"sex": "male", "age": 35, "bmi": 28, "waist_cm": 96,
      "sbp": 128, "dbp": 84,
      "labs": {"glucose": 98, "hba1c": 5.5, "creatinine": 0.95,
               "tchol": 195, "hdl": 48, "trigly": 130, "crp": 1.5,
               "hgb": 15.0, "plt": 240, "alt": 30}}),
    ("Мінімальні дані",
     "Тільки sex, age, glucose",
     {"sex": "female", "age": 45,
      "labs": {"glucose": 100}}),
]



class C:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RED = "\033[31m"
    YELLOW = "\033[33m"
    GREEN = "\033[32m"
    CYAN = "\033[36m"
    MAGENTA = "\033[35m"
    BLUE = "\033[34m"


TIER_COLORS = {
    "critical": C.RED,
    "abnormal": C.YELLOW,
    "info": C.CYAN,
    "minor": C.MAGENTA,
    "normal": C.GREEN,
}

TONE_COLORS = {
    "urgent": C.RED,
    "attention_needed": C.YELLOW,
    "normal": C.GREEN,
}

OVERALL_TIER_COLORS = {
    "very_high": C.RED,
    "high": C.RED,
    "moderate": C.YELLOW,
    "low": C.GREEN,
    "very_low": C.GREEN,
}


def print_patient(predictor, idx: int, lang: str = "uk"):
    name, descr, payload = PATIENTS[idx]
    result = predictor.predict(payload)
    report = build_narrative(result, lang=lang, payload=payload)

    print()
    print("━" * 96)
    print(f"  {C.BOLD}#{idx}  {name}{C.RESET}  {C.DIM}[{lang}]{C.RESET}")
    print(f"  {C.DIM}{descr}{C.RESET}")
    print("━" * 96)

    sex_emoji = "♀" if str(payload.get("sex", "")).lower() in ("female", "f") else "♂"
    age = payload.get("age", "?")
    overall_color = OVERALL_TIER_COLORS.get(report.overall_tier, C.RESET)
    tone_color = TONE_COLORS.get(report.tone, C.RESET)

    print(f"  Пацієнт: {sex_emoji} {age} р.   "
          f"Загальний ризик: {overall_color}{C.BOLD}{report.overall_tier}{C.RESET}   "
          f"Тон: {tone_color}{report.tone}{C.RESET}")
    print(f"  {report.summary}")
    print()

    print(f"  {C.BOLD}{C.DIM}── Ризики (N={len(report.risks)}) ──{C.RESET}")
    for r in report.risks:
        tier_color = OVERALL_TIER_COLORS.get(r["risk_tier"], C.RESET)
        bar_len = int(r["probability"] * 30)
        bar = "█" * bar_len + "░" * (30 - bar_len)
        print(f"    {tier_color}{bar}{C.RESET}  "
              f"{r['name_ua']:<30}  "
              f"{r['probability']*100:5.1f}%  "
              f"{tier_color}{r['risk_tier']:<10}{C.RESET}  "
              f"×{r['odds_ratio_vs_baseline']:.1f}")

    print()
    print(f"  {C.BOLD}{C.DIM}── Історії (N={len(report.stories)}) ──{C.RESET}")
    for s in report.stories:
        tier_color = TIER_COLORS.get(s.tier, C.RESET)
        print(f"\n  {s.icon}  {tier_color}{C.BOLD}{s.title}{C.RESET}")
        print(f"  {C.DIM}({s.tier}, severity={s.severity}){C.RESET}\n")
        for line in s.body.split("\n"):
            if line.strip():
                print(f"    {line}")
        if s.actions:
            print(f"\n    {C.BOLD}Що робити:{C.RESET}")
            for a in s.actions:
                print(f"    • {a}")
        if s.red_flags:
            print(f"\n    {C.BOLD}{C.RED}Червоні прапорці:{C.RESET}")
            for rf in s.red_flags:
                print(f"    {C.RED}!{C.RESET} {rf}")


def main():
    print(f"\n{C.BOLD}{'═' * 96}{C.RESET}")
    print(f"  {C.BOLD}HEMAX_RISK — Multi-task Disease Risk Demo{C.RESET}")
    print(f"  {C.DIM}NHANES-trained PyTorch model: 6 risks (HTN, T2DM, hi-chol, CHD, CHF, stroke){C.RESET}")
    print(f"  {C.DIM}Mean test AUC = 0.852, 1.18M parameters{C.RESET}")
    print(f"{C.BOLD}{'═' * 96}{C.RESET}")

    args = sys.argv[1:]
    lang_tokens = [a for a in args if a.lower() in ("uk", "en")]
    indices = [int(a) for a in args if a.isdigit()]
    lang = lang_tokens[0] if lang_tokens else "uk"
    indices = indices or list(range(len(PATIENTS)))

    model_path = Path(__file__).parent / "risk_api" / "weights" / "model.pt"
    predictor = RiskPredictor(model_path)

    for i in indices:
        if 0 <= i < len(PATIENTS):
            print_patient(predictor, i, lang=lang)


if __name__ == "__main__":
    main()
