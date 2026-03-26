# {% if has_diabetes %}Diabetes control needs attention{% elif hba1c and hba1c >= 6.5 %}Lab criteria for possible diabetes{% else %}Elevated diabetes risk{% endif %}
icon: 🩸
severity: medium
---
{% if has_diabetes %}
Diabetes is listed in your profile, and your current values indicate that **glycemic control needs improvement** (HbA1c {{ hba1c | default('—') }}%{% if glucose %}, glucose {{ glucose }} mg/dL{% endif %}). This **isn't a failure** — diabetes is a marathon, and adjusting therapy from time to time is normal.

{% if takes_metformin %}You take metformin — discuss with your endocrinologist whether the dose should be increased or a second agent added.{% elif on_oral_diabetics %}You take oral antidiabetics — discuss therapy review with your endocrinologist.{% elif on_insulin %}You're on insulin — discuss dose titration with your endocrinologist.{% endif %}
{% elif hba1c and hba1c >= 6.5 %}
Your lab values (HbA1c {{ hba1c }}%{% if glucose %}, glucose {{ glucose }} mg/dL{% endif %}) **meet ADA criteria for possible type 2 diabetes** (HbA1c ≥6.5% or fasting glucose ≥126 mg/dL). This is **not a final diagnosis** — confirmation requires a repeat test and clinical evaluation.
{% elif hba1c and hba1c >= 5.7 %}
Your HbA1c {{ hba1c }}% is in the **prediabetic range** (5.7-6.4%). Without intervention, 30-50% of people with prediabetes progress to diabetes within 5 years.
{% else %}
Your profile indicates **substantially elevated risk of type 2 diabetes** ({{ p_diabetes }}%, ×{{ ratio_diabetes }} the population baseline).
{% endif %}

{% if not has_diabetes %}Good news: **type 2 diabetes is largely preventable** through lifestyle changes. In the DPP trial, lifestyle change was **more effective than metformin** at preventing progression from prediabetes.{% else %}Good news: with adequate diabetes control, the risk of complications (nephropathy, retinopathy, neuropathy, CVD) is significantly reduced. Targets are individual — discuss with your endocrinologist.{% endif %}
---
actions:
{% if has_diabetes %}
- **Show results to your endocrinologist** — discuss intensifying therapy or adjusting doses
- Self-monitor glucose (fasting + postprandial) per your doctor's schedule
- Annually: ophthalmology exam, foot check, urine albumin, creatinine
- Review diet and physical activity — often more impactful than medication changes
{% if bmi and bmi >= 25 %}- Even 5% weight loss significantly improves glycemia{% endif %}
- Do NOT stop current medications on your own
{% else %}
- **See a GP or endocrinologist**
- Repeat HbA1c and fasting glucose in 6-8 weeks{% if hba1c and hba1c >= 6.5 %} to confirm the diagnosis{% endif %}
- Consider OGTT (oral glucose tolerance test) for precise diagnosis
{% if bmi and bmi >= 25 %}- 5-7% weight loss reduces diabetes risk by ~58%{% endif %}
- 150 min/week of moderate aerobic activity
- Cut fast carbs (white bread, sugary drinks, baked goods)
- Boost fiber (vegetables, legumes, whole grains)
- Consider protein + fat breakfasts instead of carb-heavy ones
{% endif %}
---
red_flags:
- Severe thirst + frequent urination + unexplained weight loss
- Fruity breath, nausea, abdominal pain — possible **DKA, go to ER**
- Non-healing wounds on feet
- Sudden vision changes
{% if has_diabetes %}- Frequent hypoglycemia (tremor, cold sweat, hunger) — needs dose adjustment{% endif %}
