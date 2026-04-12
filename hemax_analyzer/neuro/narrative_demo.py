from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from neuro_api.neuro.inference import RiskPredictor
from neuro_api.narrative.narrative_engine import build_narrative


PATIENTS = [
    ("Здорова молода жінка", "F28, athletic, нормальні показники", {
        "sex": "female", "age": 28, "bmi": 22, "waist_cm": 72,
        "sbp": 116, "dbp": 70, "pulse": 64,
        "labs": {"hgb": 13.6, "wbc": 5.4, "plt": 240, "rdw": 13.0,
                 "glucose": 88, "hba1c": 5.1, "creatinine": 0.85,
                 "alt": 18, "ast": 20, "tchol": 175, "hdl": 65, "trigly": 80,
                 "crp": 0.6, "vit_d_total": 32, "ferritin_ngml": 60}}),
    ("Жінка з прихованою анемією", "F35, low Hb, low ferritin, втома", {
        "sex": "female", "age": 35, "bmi": 23, "waist_cm": 76,
        "sbp": 108, "dbp": 68, "pulse": 84,
        "labs": {"hgb": 11.2, "wbc": 6.0, "plt": 280, "rdw": 16.5, "mcv": 78,
                 "ferritin_ngml": 8,
                 "glucose": 92, "hba1c": 5.3, "creatinine": 0.75,
                 "alt": 22, "ast": 24, "tchol": 185, "hdl": 58, "trigly": 110,
                 "crp": 1.4, "vit_d_total": 22}}),
    ("Burnout-професіонал", "M40, vit D дефіцит, високий CRP, мало сну", {
        "sex": "male", "age": 40, "bmi": 28, "waist_cm": 96,
        "sbp": 132, "dbp": 84, "pulse": 76,
        "labs": {"hgb": 14.5, "wbc": 7.2, "plt": 260, "rdw": 13.4,
                 "glucose": 96, "hba1c": 5.5,
                 "creatinine": 1.0, "alt": 30, "ast": 26,
                 "tchol": 220, "hdl": 38, "trigly": 195,
                 "crp": 4.5, "vit_d_total": 14, "ferritin_ngml": 95}}),
    ("Літня жінка-вдова", "F72, нещодавно овдовіла, соціальна ізоляція", {
        "sex": "female", "age": 72, "bmi": 26, "waist_cm": 92,
        "sbp": 142, "dbp": 80, "pulse": 78,
        "labs": {"hgb": 12.4, "wbc": 6.8, "plt": 240, "rdw": 14.8,
                 "glucose": 102, "hba1c": 5.9,
                 "creatinine": 1.1, "alt": 22, "ast": 26,
                 "tchol": 215, "hdl": 56, "trigly": 145,
                 "crp": 3.2, "vit_d_total": 18, "ferritin_ngml": 75}}),
    ("Тяжкий депресивний епізод", "F45, RDW high, CRP high, vit D + ferritin low", {
        "sex": "female", "age": 45, "bmi": 31, "waist_cm": 102,
        "sbp": 124, "dbp": 78, "pulse": 88,
        "labs": {"hgb": 11.8, "wbc": 8.0, "plt": 290, "rdw": 17.0,
                 "glucose": 98, "hba1c": 5.8,
                 "creatinine": 0.9, "alt": 38, "ast": 30,
                 "tchol": 235, "hdl": 42, "trigly": 175,
                 "crp": 6.8, "vit_d_total": 12, "ferritin_ngml": 14}}),
    ("Ймовірний sleep-apnea профіль", "M52, BMI 36, AT high, snoring", {
        "sex": "male", "age": 52, "bmi": 36, "waist_cm": 116,
        "sbp": 148, "dbp": 92, "pulse": 80,
        "labs": {"hgb": 16.2, "wbc": 7.8, "plt": 245, "rdw": 14.2,
                 "glucose": 108, "hba1c": 6.0,
                 "creatinine": 1.1, "alt": 42, "ast": 32,
                 "tchol": 215, "hdl": 36, "trigly": 220,
                 "crp": 4.2, "vit_d_total": 20}}),
    ("Сигнал suicidal ideation", "F42, високий пульс, abnormal ALP — SAFETY-CRITICAL", {
        "sex": "female", "age": 42, "bmi": 24, "waist_cm": 84,
        "sbp": 118, "dbp": 78, "pulse": 96,
        "labs": {"hgb": 12.0, "wbc": 9.4, "plt": 275, "rdw": 15.6,
                 "glucose": 92, "hba1c": 5.4,
                 "creatinine": 0.85, "alt": 28, "ast": 30,
                 "alp_ul": 145,
                 "tchol": 195, "hdl": 50, "trigly": 130,
                 "crp": 3.8, "vit_d_total": 16, "ferritin_ngml": 45,
                 "albumin_gdl": 3.6}}),
    ("Здоровий активний пенсіонер", "M68, спортивний", {
        "sex": "male", "age": 68, "bmi": 24, "waist_cm": 88,
        "sbp": 128, "dbp": 76, "pulse": 60,
        "labs": {"hgb": 14.8, "wbc": 5.6, "plt": 220, "rdw": 13.2,
                 "glucose": 94, "hba1c": 5.4,
                 "creatinine": 1.0, "alt": 22, "ast": 24,
                 "tchol": 195, "hdl": 62, "trigly": 95,
                 "crp": 1.0, "vit_d_total": 36, "ferritin_ngml": 110}}),
    ("Мінімальні дані", "Лише вік + стать + AT", {
        "sex": "female", "age": 45, "sbp": 124, "dbp": 78}),
]


class C:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RED = "\033[91m"
    YEL = "\033[93m"
    GRN = "\033[92m"


OVERALL_TIER_COLORS = {
    "very_low": C.GRN, "low": C.GRN, "moderate": C.YEL,
    "high": C.RED, "very_high": C.RED,
    "uncertain": C.DIM, "insufficient_data": C.DIM,
}


def print_patient(predictor: RiskPredictor, idx: int, lang: str = "uk"):
    title, descr, payload = PATIENTS[idx]
    print()
    print(f"{C.BOLD}{'━' * 96}{C.RESET}")
    print(f"  {C.BOLD}#{idx}  {title}{C.RESET}  {C.DIM}[{lang}]{C.RESET}")
    print(f"  {C.DIM}{descr}{C.RESET}")
    print(f"{C.BOLD}{'━' * 96}{C.RESET}")

    result = predictor.predict(payload)
    report = build_narrative(result, lang=lang, payload=payload)

    sex_raw = payload.get("sex", "")
    sex_emoji = "♀" if str(sex_raw).lower() in ("female", "f", "ж") else "♂"
    age = payload.get("age", "?")
    overall_color = OVERALL_TIER_COLORS.get(report.overall_tier, C.RESET)
    print(f"  Пацієнт: {sex_emoji} {age} р.   "
          f"Загальний ризик: {overall_color}{report.overall_tier}{C.RESET}   "
          f"Тон: {C.BOLD}{report.tone}{C.RESET}")
    print(f"  {report.summary}")
    print()

    print(f"  {C.BOLD}{C.DIM}── Ризики (N={len(report.risks)}) ──{C.RESET}")
    for r in report.risks:
        tier_color = OVERALL_TIER_COLORS.get(r["risk_tier"], C.RESET)
        bar_len = int(r["probability"] * 30)
        bar = "█" * bar_len + "░" * (30 - bar_len)
        print(f"    {tier_color}{bar}{C.RESET}  "
              f"{r['name_ua']:<28}  "
              f"{r['probability']*100:5.1f}%  "
              f"{tier_color}{r['risk_tier']:<10}{C.RESET}  "
              f"×{r['odds_ratio_vs_baseline']:.1f}")
        drivers = result.top_drivers.get(r["target"], [])[:3]
        if drivers:
            parts = []
            for d in drivers:
                v_str = f"{d.value:.1f}" if d.value is not None else "n/a"
                arrow = "↑" if d.direction == "raises" else "↓" if d.direction == "lowers" else "·"
                parts.append(f"{d.feature}={v_str}{arrow}")
            print(f"      {C.DIM}↳ {' · '.join(parts)}{C.RESET}")

    if report.stories:
        print()
        print(f"  {C.BOLD}{C.DIM}── Історії (N={len(report.stories)}) ──{C.RESET}")
        for s in report.stories:
            tier_color = C.RED if s.tier == "critical" else C.YEL if s.tier == "abnormal" else C.GRN
            print()
            print(f"  {s.icon}  {C.BOLD}{tier_color}{s.title}{C.RESET}")
            print(f"  {C.DIM}({s.tier}, severity={s.severity}){C.RESET}")
            print()
            for line in s.body.split("\n"):
                print(f"    {line}")
            if s.actions:
                print()
                print(f"    {C.BOLD}Що робити:{C.RESET}")
                for a in s.actions:
                    print(f"    • {a}")
            if s.red_flags:
                print()
                print(f"    {C.BOLD}{C.RED}Червоні прапорці:{C.RESET}")
                for rf in s.red_flags:
                    print(f"    {C.RED}!{C.RESET} {rf}")


def main():
    print(f"\n{C.BOLD}{'═' * 96}{C.RESET}")
    print(f"  {C.BOLD}HEMAX_NEURO — Mental Health & Sleep Multi-task Demo{C.RESET}")
    print(f"  {C.DIM}NHANES-trained PyTorch: 5 tasks (depression, sleep, suicidal ideation){C.RESET}")
    print(f"  {C.DIM}Mean test AUC = 0.630, 1.16M parameters{C.RESET}")
    print(f"{C.BOLD}{'═' * 96}{C.RESET}")

    args = sys.argv[1:]
    lang_tokens = [a for a in args if a.lower() in ("uk", "en")]
    indices = [int(a) for a in args if a.isdigit()]
    lang = lang_tokens[0] if lang_tokens else "uk"
    indices = indices or list(range(len(PATIENTS)))

    model_path = Path(__file__).parent / "neuro_api" / "weights" / "model.pt"
    predictor = RiskPredictor(model_path)

    for i in indices:
        if 0 <= i < len(PATIENTS):
            print_patient(predictor, i, lang=lang)


if __name__ == "__main__":
    main()
