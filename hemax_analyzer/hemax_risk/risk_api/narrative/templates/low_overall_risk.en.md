# {% if has_any_chronic and on_any_therapy %}Therapy is working — keep monitoring{% elif has_any_chronic %}Profile stable — keep monitoring{% else %}Low overall risk{% endif %}
icon: {% if has_any_chronic %}📈{% else %}✅{% endif %}
severity: low
---
{% if has_any_chronic and on_any_therapy %}
All six scores (hypertension, diabetes, cholesterol, CHD, heart failure, stroke) are at or below population average at this time.

**This does NOT mean your risk is gone.** You have a chronic condition in your profile{% if on_statins %}, and **statins are making your lipid panel look normal** — without them, values would be substantially worse{% endif %}{% if on_acei_arb or on_antihypertensives %}{% if on_statins %};{% else %}, and{% endif %} **antihypertensive therapy is keeping BP under control** — without it, heart attack/stroke risk would be much higher{% endif %}{% if takes_metformin or on_oral_diabetics or on_insulin %}{% if on_statins or on_acei_arb or on_antihypertensives %};{% else %}, and{% endif %} **glucose-lowering therapy is keeping blood sugar under control**{% endif %}.

**Therapy is working — that's what matters most.** Current results reflect **treatment success**, not disease disappearance. Keep taking medications and attending regular visits.
{% elif has_any_chronic %}
All six scores are at or below population average at this time. You have a chronic condition in your profile, and **current numbers are stable** — a positive result.

However, **this does NOT mean risk is gone**. Continue regular monitoring, preventive visits, and a healthy lifestyle. If your physician prescribes therapy, discuss it.
{% else %}
Overall chronic disease risk is **low**. All six scores (hypertension, diabetes, cholesterol, CHD, heart failure, stroke) are at or below population average.

Based on the values you provided, the profile does not indicate elevated risk in the evaluated domains.
{% endif %}
---
actions:
{% if has_any_chronic and on_any_therapy %}
- **Do NOT stop current therapy on your own** — that's the leading cause of decompensation in chronic disease
- Regular visits to the prescribing physician — don't skip control labs
- Maintain the lifestyle and diet that give you this stability
- Regular activity 150 min/week
- Home monitoring of BP, glucose, or your relevant marker{% if has_diabetes %} (home glucose meter){% endif %}
{% elif has_any_chronic %}
- Regular physician visits — discuss whether current values mean therapy isn't needed, or whether risk is drifting into a safer zone
- Home monitoring of BP, glucose, or your relevant marker
- Regular activity 150 min/week
- Balanced diet, don't neglect sleep and stress
{% else %}
- Annual preventive check
- Maintain current lifestyle
- Regular activity 150 min/week
- Balanced diet
- BP check annually
- Don't neglect sleep and stress
{% endif %}
---
red_flags:
- New symptoms — don't ignore even with low risk
{% if has_any_chronic %}- Sudden worsening on current therapy — see a physician urgently{% endif %}
