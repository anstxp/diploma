#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import sys
import os
from pathlib import Path

_here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _here)
sys.path.insert(0, os.path.abspath(os.path.join(_here, "..", "chem_phase4")))

_mpt_path = Path(__file__).with_name("manual_patient_test.py")
spec = importlib.util.spec_from_file_location("mpt", _mpt_path)
mpt = importlib.util.module_from_spec(spec); spec.loader.exec_module(mpt)
PATIENTS = mpt.PATIENTS


BOLD   = "\033[1m"; DIM = "\033[2m"
GREEN  = "\033[32m"; BLUE = "\033[34m"; YELLOW = "\033[33m"; RED = "\033[31m"
MAGENTA= "\033[35m"; CYAN = "\033[36m"; GREY = "\033[90m"
RESET  = "\033[0m"

TIER_STYLE = {
    "critical": (RED,     "🔴"),
    "abnormal": (YELLOW,  "⚠️ "),
    "info":     (BLUE,    "ℹ️ "),
    "minor":    (CYAN,    "ℹ️ "),
    "normal":   (GREEN,   "✅"),
}


def _wrap(text: str, width: int = 88, indent: str = "     ") -> str:
    out_lines = []
    for para in text.split("\n\n"):
        for raw_line in para.split("\n"):
            words = raw_line.strip().split()
            if not words:
                continue
            cur = indent
            for w in words:
                candidate = (cur + " " + w) if cur.strip() else cur + w
                if len(candidate) > width and cur.strip():
                    out_lines.append(cur.rstrip())
                    cur = indent + w
                else:
                    cur = candidate
            if cur.strip():
                out_lines.append(cur.rstrip())
        out_lines.append("")
    return "\n".join(out_lines).rstrip()


def _print_report(title: str, descr: str, report, lang: str):
    from chem_api.narrative import chrome
    ch = chrome(lang)
    print()
    print("━" * 96)
    print(f"{BOLD}{title}{RESET}   {DIM}[{lang}]{RESET}")
    print(f"{DIM}{descr}{RESET}")
    print()
    tone_color = {"urgent": RED, "attention_needed": YELLOW, "normal": GREEN}[report.tone]
    print(f"  {tone_color}{BOLD}{report.summary}{RESET}")
    if report.patient.get("age") is not None:
        sex_disp = {"female": "♀", "male": "♂"}.get(report.patient.get("sex"), "")
        print(f"  {DIM}Пацієнт: {sex_disp} {report.patient.get('age'):.0f} р.{RESET}" if lang == "uk"
              else f"  {DIM}Patient: {sex_disp} {report.patient.get('age'):.0f} y.o.{RESET}")
    print()

    for story in report.stories:
        color, _ = TIER_STYLE.get(story.tier, (RESET, "•"))
        print(f"  {color}{story.icon}  {BOLD}{story.title}{RESET}")
        print(f"     {DIM}({story.tier}, severity={story.severity}){RESET}")
        print()
        print(_wrap(story.body, width=92, indent="     "))
        print()
        if story.actions:
            print(f"     {BOLD}{ch['actions_header']}:{RESET}")
            for a in story.actions:
                print(f"     • {_wrap(a, width=88, indent='       ').lstrip()}")
            print()
        if story.red_flags:
            print(f"     {RED}{BOLD}{ch['red_flags_header']}:{RESET}")
            for rf in story.red_flags:
                print(f"     {RED}!{RESET} {_wrap(rf, width=88, indent='       ').lstrip()}")
            print()

    print(f"  {DIM}{ch['this_is_not_diagnosis']}{RESET}")


def main():
    from chem_api.chem.analyze import analyze_chem_payload
    from chem_api.narrative import build_narrative

    args = sys.argv[1:]
    lang_tokens = [a for a in args if a.strip("-").lower() in ("uk", "en")]
    index_tokens = [a for a in args if a not in lang_tokens and not a.startswith("--")]

    try:
        pick = [int(x) for x in index_tokens] if index_tokens else None
    except ValueError as e:
        sys.exit(f"invalid patient index: {e}. Usage: narrative_demo.py [uk|en] [index ...]")

    langs = [a.strip("-").lower() for a in lang_tokens] if lang_tokens else ["uk"]

    indices = pick if pick else list(range(len(PATIENTS)))

    for lang in langs:
        print()
        print("╔" + "═" * 94 + "╗")
        lang_label = "УКРАЇНСЬКОЮ" if lang == "uk" else "ENGLISH"
        padding = (94 - len(lang_label)) // 2
        print("║" + " " * padding + lang_label + " " * (94 - padding - len(lang_label)) + "║")
        print("╚" + "═" * 94 + "╝")
        for idx in indices:
            title, descr, payload = PATIENTS[idx]
            raw = analyze_chem_payload(payload)
            report = build_narrative(raw, lang=lang)
            _print_report(title, descr, report, lang)


if __name__ == "__main__":
    main()
