# Circadian disruption from shift work
icon: 🌗
severity: medium
---
You reported working a shift schedule. This is a **standalone risk factor** for:
- **Metabolic syndrome** (×1.4 type-2 diabetes risk)
- **Cardiovascular events** (×1.3 CHD risk)
- **Depression and anxiety**
- **Breast cancer** (in women — IARC classes shift work as probable carcinogen 2A)
- **Cognitive impairment** with long-term shift work

This does **not** mean shift work is "bad" — millions work shifts and live long lives. But **your body needs extra protection** that day-workers don't.

**Why?** The circadian rhythm controls hundreds of physiologic processes: insulin secretion, cortisol release, body temperature, melatonin synthesis, DNA repair. **The cycle never fully adapts** to a shifted schedule, even after years. Each night shift is a mini-jetlag.

{% if sleep_hours_avg and sleep_hours_avg < 7 %}You sleep {{ sleep_hours_avg }}h — this **amplifies** shift-work risks. <7h + shifts = doubled metabolic risk.
{% endif %}
{% if has_diabetes %}Diabetes + shift work makes glycemic control harder — glucose levels don't "know" when you sleep or eat.
{% endif %}
{% if bmi and bmi > 27 %}Excess weight + shift work is a critical combo for sleep apnea.
{% endif %}
---
actions:
- **Post-night-shift sleep strategy:**
  - Dark (blackout curtains) quiet room
  - No heavy meal 2h before sleep
  - Earplugs or white noise — daytime quiet is rare
- **Light therapy**: 10,000 lux bright light for 30 min at the start of your "active" phase — the most powerful circadian regulator
- **Avoid bright light** before your sleep period (even if "morning" for everyone else) — blue-blocking glasses, dim home lighting
- **Melatonin 0.5-3 mg** 30 min before intended sleep — cheap, safe supplement to shift the rhythm (discuss with doctor before regular use)
- **Eating schedule**: eat in your "day" phase, **don't eat during the night shift** (disrupts metabolic hormones)
- **Exercise**: at shift start helps wake up, **not 2h before sleep**
- **Caffeine**: OK at shift start, **none in the second half**
- **Annual check-ups**: BP, glucose/HbA1c, lipids, TSH — shift workers need these more often
- If possible — minimize rotation between morning↔night (worse than stable night shifts)
---
red_flags:
- Falling asleep on the way to/from work — **pull over, nap 20 min**
- Chronic fatigue that doesn't resolve on days off — screen for apnea, depression
- Metabolic problems (BP, glucose, weight) — discuss schedule changes with your doctor
- Depression symptoms — shift workers have 2× risk; don't ignore
