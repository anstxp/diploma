# {% if has_hypertension %}Hypertension control needs attention{% else %}Elevated hypertension risk{% endif %}
icon: 💓
severity: medium
---
{% if has_hypertension %}
Hypertension is listed in your profile. {% if sbp and sbp >= 140 %}Current BP ({{ sbp }}/{{ dbp }}) is above target **even on therapy** — meaning **control is inadequate**.{% elif sbp and sbp >= 130 %}Current BP ({{ sbp }}/{{ dbp }}) is in the "high-normal" range — close to target but needs monitoring.{% else %}Current BP numbers are normal — therapy is working, continue it consistently.{% endif %}

{% if on_acei_arb or on_diuretics or on_antihypertensives %}You're on antihypertensive therapy. **Do NOT stop medications on your own**, even if numbers look normal — that's the most common cause of hypertensive crises and strokes in known hypertensives.{% endif %}
{% else %}
Analysis indicates **substantial risk of hypertension** ({{ p_htn }}%, ×{{ ratio_htn }}). {% if sbp and sbp >= 140 %}Elevated BP already recorded ({{ sbp }}/{{ dbp }}).{% elif sbp and sbp >= 130 %}BP is in the "high-normal" range ({{ sbp }}/{{ dbp }}).{% endif %}

Hypertension is the **single most modifiable risk factor** for stroke and heart attack. It often runs without symptoms — hence "silent killer".
{% endif %}
---
actions:
{% if has_hypertension %}
- **Home BP monitoring** — twice daily for 7 days, log results
- **Show results to your physician** — discuss intensifying or adjusting therapy
{% if sbp and sbp >= 140 %}- BP consistently >140/90 on therapy = **resistant hypertension** — discuss with cardiologist{% endif %}
- Check serum potassium if you take ACEI/ARB or potassium-sparing diuretics
- Reduce salt to <5 g/day (<1 tsp)
- Take medications consistently — don't skip, don't self-adjust doses
{% else %}
- **Home BP monitoring** — twice daily for 7 days, log results
- See a GP with the log
- Reduce salt to <5 g/day (<1 tsp)
- DASH diet (fruits, veggies, low-fat dairy, low saturated fat)
- 150 min/week aerobic activity
{% if bmi and bmi >= 25 %}- Even 5 kg weight loss lowers BP{% endif %}
- Limit alcohol, ideally quit smoking
- If medication is prescribed, take consistently
{% endif %}
---
red_flags:
- Severe headache, nausea, visual changes, confusion — hypertensive crisis
- Chest pain
- BP ≥180/120 is an emergency
{% if has_hypertension %}- Sudden one-sided weakness/slurred speech — possible stroke, **call 911/112**{% endif %}
