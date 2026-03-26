# {% if has_diabetes %}Diabetes control — model shows moderate risk{% else %}Elevated diabetes risk{% endif %}
icon: 🩸
severity: low
---
{% if has_diabetes %}
Diabetes is in your profile, current model risk is moderate ({{ p_diabetes }}%, ×{{ ratio_diabetes }}). This means **glycemia is staying within range**, with room to optimize{% if takes_metformin or on_oral_diabetics %} current glucose-lowering therapy{% endif %}.
{% else %}
Moderately elevated diabetes risk ({{ p_diabetes }}%, ×{{ ratio_diabetes }}). No other major findings.

Early intervention is highly effective — most people in this zone can return to fully normal values.
{% endif %}
---
actions:
{% if has_diabetes %}
- HbA1c every 3 months; fasting/postprandial glucose per your doctor's schedule
- Home glucose self-monitoring
- Endocrinologist visits every 3-6 months
- Diet and physical activity — foundation of control
{% if bmi and bmi >= 25 %}- Weight loss helps glycemic control{% endif %}
- Do not stop medications on your own
{% else %}
- Annual HbA1c and fasting glucose
- Regular physical activity, even simple walking
- Cut fast carbs
{% if bmi and bmi >= 25 %}- Weight loss is the primary intervention{% endif %}
{% endif %}
---
red_flags:
- New thirst, frequent urination
{% if has_diabetes %}- Frequent hypoglycemia
- Sudden vision changes, non-healing foot wounds{% endif %}
