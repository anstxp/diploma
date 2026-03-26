# {% if on_statins %}Statin therapy insufficient{% elif has_high_chol %}Lipid control needs attention{% else %}Elevated dyslipidemia risk{% endif %}
icon: 💗
severity: medium
---
{% if on_statins %}
You're on statins, but the lipid panel remains atherogenic ({{ p_high_chol }}%, ×{{ ratio_high_chol }}). This means **current therapy is insufficient**. Don't panic: statins work well on LDL but have limited effect on HDL and triglycerides. The regimen needs review with a cardiologist.

{% if tchol and tchol >= 200 %}Total cholesterol {{ tchol }} mg/dL on statins — discuss increasing the dose or adding ezetimibe.{% endif %}
{% elif has_high_chol %}
Hypercholesterolemia is in your profile, and the current lipid panel remains atherogenic ({{ p_high_chol }}%, ×{{ ratio_high_chol }}). If you're not on statins, discuss therapy with a cardiologist; if this is a new diagnosis, current values confirm the need for intervention.
{% else %}
Profile shows **substantial dyslipidemia risk** ({{ p_high_chol }}%, ×{{ ratio_high_chol }}). {% if tchol and tchol >= 200 %}Total cholesterol {{ tchol }} mg/dL is elevated.{% endif %}{% if hdl and hdl < 40 and is_male %} HDL {{ hdl }} is below 40 in a male — an added risk factor.{% elif hdl and hdl < 50 and is_female %} HDL {{ hdl }} is below 50 in a female — an added risk factor.{% endif %}

Cholesterol is the **single best-evidenced driver of atherosclerosis**. The "good/bad" framing is simplified but the core idea holds.
{% endif %}

{% if has_diabetes %}You have diabetes, so **LDL targets are stricter**: <70 mg/dL at high risk, <55 mg/dL at very high risk (prior CV event, target-organ damage).{% endif %}
{% if has_cardiovascular_disease %}Since you've had a cardiovascular event, **secondary prevention with an aggressive LDL <55 mg/dL** target is indicated.{% endif %}
---
actions:
{% if on_statins %}
- **See a cardiologist** — discuss intensifying therapy (higher dose, ezetimibe, fibrates, omega-3 for high TG)
- Check compliance: are you taking statins consistently, at the right time?
- Check ALT and creatine kinase — confirm current dose isn't causing side effects
- Review diet and physical activity — critical even on statins
- Consider Lp(a) once — hereditary factor
{% else %}
- Repeat fasting lipid panel (≥9h fast) to confirm
- See a GP or cardiologist
- Consider Lp(a) (hereditary risk factor) once
- Diet: less saturated fat, more fiber, omega-3 (fish, nuts)
{% if bmi and bmi >= 25 %}- Weight loss improves all lipid markers{% endif %}
- 150 min/week aerobic activity
- Discuss statin therapy if ASCVD risk ≥7.5%
{% endif %}
---
red_flags:
- Chest pain on exertion
- Yellow nodules on skin (xanthomas) — possible familial form
- Calf pain on walking — peripheral arterial disease
{% if on_statins %}- Severe muscle pain or dark urine — **possible statin rhabdomyolysis** — urgent medical attention{% endif %}
