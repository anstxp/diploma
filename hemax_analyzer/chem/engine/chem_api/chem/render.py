from __future__ import annotations

from typing import Dict, List


def render_text(report: Dict) -> str:
    lines: List[str] = []
    s = report.get("summary", {})
    lines.append(f"🧾 {s.get('headline','')}")
    for n in s.get("notes", []):
        lines.append(f"- {n}")

    lines.append("\n=== СИГНАЛИ / КОМБІНАЦІЇ ===")
    for sig in report.get("signals", []):
        lines.append(f"\n[{sig.get('severity','')}] {sig.get('title', sig.get('id',''))}")
        why = sig.get("why")
        if why:
            lines.append(f"Чому: {why}")
        ev = sig.get("evidence")
        if ev:
            lines.append(f"Дані: {ev}")
        nxt = sig.get("next", [])
        if nxt:
            lines.append("Що робити далі:")
            for x in nxt:
                lines.append(f"  • {x}")

    lines.append("\n=== КОЖЕН ПОКАЗНИК (пояснення) ===")
    for lab in report.get("labs", []):
        lines.append(
            f"\n{lab.get('name')} ({lab.get('code')}): {lab.get('value')} {lab.get('unit','')}"
            f"  | ref {lab.get('ref')}  | flag={lab.get('flag')}"
        )
        what = lab.get("what")
        if what:
            lines.append(f"Що це: {what}")
        for t in lab.get("interpretation", []):
            lines.append(f"Інтерпретація: {t}")
        tips = lab.get("tips", [])
        if tips:
            lines.append("Поради:")
            for x in tips:
                lines.append(f"  • {x}")
        cav = lab.get("caveats", [])
        if cav:
            lines.append("Застереження:")
            for x in cav:
                lines.append(f"  • {x}")

    d = report.get("derived", {})
    if d:
        lines.append("\n=== ПОХІДНІ РОЗРАХУНКИ ===")
        for k, v in d.items():
            lines.append(f"- {k}: {v}")

    disc = report.get("disclaimer")
    if disc:
        lines.append(f"\n⚠️ {disc}")
    return "\n".join(lines)
