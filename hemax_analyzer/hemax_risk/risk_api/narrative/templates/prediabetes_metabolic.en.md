# {% if has_diabetes %}Stable glycemic control — keep monitoring{% else %}Moderate metabolic risk{% endif %}
icon: ⚖️
severity: medium
---
{% if has_diabetes %}
Diabetes is already in your profile, and current model risk is moderate ({{ p_diabetes }}%). This is **positive** — it means your glucose control is fairly stable{% if takes_metformin or on_oral_diabetics or on_insulin %}, and glucose-lowering therapy is working{% endif %}.

However, this is not diabetes "going away" — continue monitoring, taking medications, and regular endocrinologist visits.
{% else %}
Your profile indicates **moderate risk of developing diabetes** ({{ p_diabetes }}%, ×{{ ratio_diabetes }}). This is the **prediabetes zone** — not disease yet, but no longer fully normal.

This is a signal to act **now**, not wait. Most people with this profile can **return to full normal** within 6-12 months through simple lifestyle changes.
{% endif %}
---
actions:
{% if has_diabetes %}
- Continue regular endocrinologist visits — every 3-6 months
- HbA1c every 3 months (standard monitoring)
- Home glucose self-monitoring per your doctor's schedule
- Annually: ophthalmology exam, foot check, urine ACR, creatinine
- Do not stop current medications on your own
{% else %}
- Annual HbA1c and fasting glucose
{% if bmi and bmi >= 25 %}- 5-7% weight loss dramatically reduces risk{% endif %}
- At least 30 min walking/day
- Cut sugar and fast carbs
- Get enough sleep — sleep deficit worsens glucose tolerance
- Manage stress — cortisol raises glucose
{% endif %}
---
red_flags:
- Severe thirst, frequent urination
{% if not has_diabetes %}- Sudden weakness after eating — diabetes can progress quickly{% else %}- Frequent hypoglycemia (tremor, cold sweat, hunger) — needs dose adjustment
- Sudden vision changes or limb numbness{% endif %}
