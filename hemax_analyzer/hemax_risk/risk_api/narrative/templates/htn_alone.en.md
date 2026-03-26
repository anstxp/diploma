# {% if on_acei_arb or on_antihypertensives %}Antihypertensive therapy is working — standard monitoring{% elif has_hypertension %}Hypertension controlled by lifestyle — keep it up{% else %}Moderately elevated hypertension risk{% endif %}
icon: 💓
severity: low
---
{% if on_acei_arb or on_antihypertensives %}
You're on antihypertensive therapy, and current model risk is moderate ({{ p_htn }}%). **This means therapy is keeping BP under control** — without it, numbers would be substantially higher.

{% if sbp and sbp < 130 %}Current BP {{ sbp }}/{{ dbp }} is at target — continue current regimen.{% elif sbp and sbp >= 130 and sbp < 140 %}BP {{ sbp }}/{{ dbp }} is close to target — discuss with doctor whether adjustment is needed.{% elif sbp and sbp >= 140 %}BP {{ sbp }}/{{ dbp }} is above target on therapy — discuss intensification.{% endif %}
{% elif has_hypertension %}
Hypertension is in your profile, but current model risk is moderate ({{ p_htn }}%). If you're keeping BP under control without meds — that's **your work paying off**, keep going.
{% else %}
**Moderately elevated hypertension risk** ({{ p_htn }}%, ×{{ ratio_htn }}). Other CV risks are normal — encouraging.

At this stage, interventions are particularly effective: lifestyle can keep BP in range **without medications**.
{% endif %}
---
actions:
{% if on_acei_arb or on_antihypertensives %}
- **Take medications consistently** — don't skip, don't self-adjust
- Home BP monitor every 1-2 weeks — keep a log
- Regular activity 150 min/week
- Reduce salt and alcohol
- Follow-up with physician every 3-6 months
{% if on_acei_arb %}- Check serum potassium every 6-12 months{% endif %}
{% else %}
- Home BP monitor every 1-2 weeks
- Reduce salt and alcohol
- Regular activity 150 min/week
- Weight control {% if bmi and bmi >= 25 %}— excess weight raises BP{% endif %}
- Quit smoking if you smoke
- Annual GP visit
{% endif %}
---
red_flags:
- Systolic BP >160 — needs medical evaluation
- Sudden symptom changes
{% if on_acei_arb %}- Dry cough — common ACEI side effect; discuss switch to ARB
- Muscle weakness, irregular heartbeat — possible hyperkalemia{% endif %}
