# {% if has_chf %}Heart failure control{% elif has_cardiovascular_disease %}Elevated risk of progression to heart failure{% else %}Elevated heart failure risk{% endif %}
icon: 💔
severity: high
---
{% if has_chf %}
Heart failure is in your profile, and current model shows **elevated risk** ({{ p_chf }}%). This means **compensatory mechanisms are under strain** — therapy review is needed.

{% if on_acei_arb or on_antihypertensives %}You're on foundational therapy — **do not stop medications on your own**, discuss intensification with your cardiologist (possibly dose titration or adding SGLT2/MRA).{% endif %}
{% elif has_cardiovascular_disease %}
You already have CVD in your profile, and the model shows **elevated risk of progression to heart failure** ({{ p_chf }}%). This is a **preventive warning** — act now, before symptoms appear.
{% else %}
Analysis shows **elevated heart failure risk** ({{ p_chf }}%, ×{{ ratio_chf }}). Heart failure is when the heart can't pump blood effectively for the body's needs.

Prevention works best before symptoms appear.
{% endif %}
---
actions:
{% if has_chf %}
- **Cardiologist — unscheduled visit** to review the regimen
- Echocardiogram for repeat ejection-fraction assessment
- BNP/NT-proBNP — compare with prior values
- Daily weight — sudden ≥1 kg/day gain = fluid retention
- Salt/fluid restriction per your physician
- **Do not skip medications** — leading cause of decompensation
{% elif has_cardiovascular_disease %}
- **Cardiologist within 1-2 months**
- Echocardiogram for ejection-fraction baseline
- BNP or NT-proBNP — baseline for future monitoring
- Tight control of BP, lipids, glycemia
- Regular moderate activity — discuss cardiac rehab with physician
{% else %}
- **Cardiologist within 1-2 months**
- Echocardiogram for ejection-fraction assessment
- BNP or NT-proBNP — heart failure marker
- BP and pulse monitoring
- Salt/fluid restriction per physician
- Regular moderate activity
{% endif %}
---
red_flags:
- Shortness of breath at rest or at night (orthopnea)
- Leg swelling by end of day
- Rapid weight gain (≥1 kg/day = fluid retention)
- Cough with pink/frothy sputum
- Palpitations, irregular heartbeat
