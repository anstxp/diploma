# {% if has_any_chronic %}Chronic disease control is stable{% else %}Moderate cardiometabolic risk{% endif %}
icon: ⚖️
severity: medium
---
{% if has_any_chronic %}
You have a chronic condition in your profile, and current model assessment shows **moderate risk** across multiple domains. This means **control is stable**{% if on_any_therapy %}, with room to optimize therapy{% endif %}.

This **does not mean risk is gone** — continue regular monitoring, do not stop current medications on your own.
{% else %}
**Several systems are at moderately elevated risk**. No single abnormality is catastrophic, but together they form a characteristic phenotype worth attention.

This is **the zone where things can still be turned around** — through lifestyle alone, without medications. Without correcting risk factors, the probability of an unfavorable profile may grow with time.
{% endif %}
---
actions:
{% if has_any_chronic %}
- GP or specialist — planned visit in 1-3 months
- Repeat core labs in 3-6 months for trend
- 150 min aerobic activity/week
{% if bmi and bmi >= 25 %}- 5-10% weight loss meaningfully reduces all risks{% endif %}
- Mediterranean diet
- **Continue current therapy** consistently
{% else %}
- GP within 1-2 months
- Repeat core labs in 3-6 months for trend
- 150 min aerobic activity/week
{% if bmi and bmi >= 25 %}- 5-10% weight loss meaningfully reduces all risks{% endif %}
- Mediterranean diet
- Sleep (7-9h)
- Stress management
- Regular home BP monitoring
{% endif %}
---
red_flags:
- Chest pain, shortness of breath
- Any sudden symptom change
