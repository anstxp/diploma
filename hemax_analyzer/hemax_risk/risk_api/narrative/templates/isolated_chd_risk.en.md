# {% if has_cardiovascular_disease %}Secondary CHD prevention{% else %}Elevated coronary heart disease risk{% endif %}
icon: 🫀
severity: high
---
{% if has_cardiovascular_disease %}
You already have cardiovascular disease in your profile, and current model assessment shows **elevated CHD risk** ({{ p_chd }}%, ×{{ ratio_chd }}). This means an **unscheduled secondary-prevention review** is needed — targets are stricter than for primary prevention.

{% if on_statins or on_acei_arb or on_antihypertensives %}You're on preventive therapy — **do not stop medications on your own**. Discuss intensification with your cardiologist.{% endif %}
{% else %}
**Elevated coronary heart disease (CHD) risk** ({{ p_chd }}%, ×{{ ratio_chd }} vs population). CHD is narrowing of heart arteries due to atherosclerosis.

Risk doesn't mean current disease — it's a signal for further evaluation.
{% endif %}
---
actions:
{% if has_cardiovascular_disease %}
- **Cardiologist — unscheduled visit** to review secondary prevention
- If not done recently — ECG, echocardiogram, possibly CT coronary angiography
- Targets: LDL <55 mg/dL, BP <130/80
- Antiplatelet therapy (aspirin/clopidogrel) — per physician
- **Do not skip current medications** — leading cause of recurrent events
{% else %}
- **Cardiologist within 2-4 weeks**
- Resting ECG, possibly stress test or CT coronary calcium (CAC) score
- Full lipid panel + Lp(a)
- BP monitoring
- Discuss preventive statins and aspirin
- Activity, diet, smoking cessation — essential
{% endif %}
---
red_flags:
- Chest pain/pressure at rest or on exertion — **call 911/112 if radiating to arm/jaw**
- Jaw or left-shoulder pain
- New shortness of breath with previously easy activities
- Sudden dizziness
