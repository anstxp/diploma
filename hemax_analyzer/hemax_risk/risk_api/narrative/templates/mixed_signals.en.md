# Mixed signals
icon: 📊
severity: low
---
Your profile doesn't match any standard risk pattern cleanly. This could mean a healthy profile, or that any abnormalities are too mild or scattered to stand out.

Calculated probabilities across the six risks:
- Hypertension: {{ p_htn }}%
- Diabetes: {{ p_diabetes }}%
- High cholesterol: {{ p_high_chol }}%
- CHD: {{ p_chd }}%
- Heart failure: {{ p_chf }}%
- Stroke: {{ p_stroke }}%

{% if has_any_chronic %}You have a chronic condition in your profile — if any of these numbers is higher than your usual trend, discuss with your physician.{% else %}If any of these numbers is substantially higher than the average for your age and sex, it's worth discussing with a GP.{% endif %}
---
actions:
- Preventive GP visit{% if has_any_chronic %} — compare current values to your usual trend{% endif %}
- Healthy lifestyle is the best strategy without clear abnormalities
{% if has_any_chronic %}- Do NOT stop current therapy without discussing with your physician{% endif %}
---
red_flags:
- Any new symptoms
