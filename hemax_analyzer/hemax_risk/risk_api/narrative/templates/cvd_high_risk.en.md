# {% if has_cardiovascular_disease %}Secondary prevention of cardiovascular events{% else %}Elevated cardiovascular risk{% endif %}
icon: 🫀
severity: high
---
{% if has_cardiovascular_disease %}
You already have cardiovascular disease, and the current profile indicates **elevated risk of a recurrent event** (heart attack, stroke, heart failure progression). This means **secondary prevention needs review** — targets are stricter than for primary prevention.

Key risks:
{% if tier_chd in ['high','very_high'] %}- Coronary heart disease: {{ p_chd }}% (×{{ ratio_chd }}){% endif %}
{% if tier_chf in ['high','very_high'] %}- Heart failure: {{ p_chf }}% (×{{ ratio_chf }}){% endif %}
{% if tier_stroke in ['high','very_high'] %}- Stroke: {{ p_stroke }}% (×{{ ratio_stroke }}){% endif %}

{% if on_statins or on_acei_arb or on_antihypertensives %}You're on preventive therapy — **do NOT stop medications on your own**, discuss intensification with your cardiologist.{% else %}If you're not yet on preventive therapy (statins, ACEI/ARB, antiplatelet) — discuss this urgently with your cardiologist.{% endif %}
{% else %}
Your profile indicates **significantly elevated risk of cardiovascular events** — heart attack, stroke, or heart failure. This isn't a guarantee — it's a signal that prevention now will pay off most.

Key risks:
{% if tier_chd in ['high','very_high'] %}- Coronary heart disease: {{ p_chd }}% (×{{ ratio_chd }}){% endif %}
{% if tier_chf in ['high','very_high'] %}- Heart failure: {{ p_chf }}% (×{{ ratio_chf }}){% endif %}
{% if tier_stroke in ['high','very_high'] %}- Stroke: {{ p_stroke }}% (×{{ ratio_stroke }}){% endif %}

Most cardiovascular risks build over years — and **effective prevention works even at later stages**.
{% endif %}
---
actions:
- **See a cardiologist{% if has_cardiovascular_disease %} — unscheduled visit to review secondary prevention{% else %} within 2-3 weeks{% endif %}**
- Resting ECG, possibly stress test or echocardiogram
- Home BP monitoring
- Lipid panel + Lp(a) once
- Regular physical activity — gradually if not used to it
{% if bmi and bmi >= 30 %}- Weight management is a priority{% endif %}
{% if has_cardiovascular_disease %}
- Secondary prevention targets: LDL <55 mg/dL, BP <130/80, HbA1c <7% (if diabetic)
- Antiplatelet therapy (aspirin/clopidogrel) — per cardiologist
- Don't skip current medications — that's the **leading cause of recurrent events**
{% else %}
- Discuss preventive statin therapy
- If you have additional risk factors (diabetes, smoking, family history) — get an ASCVD risk score
{% endif %}
---
red_flags:
- Chest pain at rest or during exertion — **call 911/112 if radiating to arm/neck/jaw**
- Sudden shortness of breath, leg swelling
- Palpitations, irregular heartbeat
- One-sided weakness or slurred speech — possible stroke, **call 911/112 immediately**
- Loss of consciousness
