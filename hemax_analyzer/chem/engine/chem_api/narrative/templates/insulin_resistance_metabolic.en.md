# {% if has_diabetes %}Diabetic metabolic profile — needs attention{% else %}Insulin resistance and fatty liver pattern{% endif %}
icon: 🍔
severity: medium
---
{% if has_diabetes %}
The combination in your results — elevated triglycerides, low HDL{% if alt %}, mildly elevated ALT ({{ alt }} U/L){% endif %} — is typical of **diabetic metabolic syndrome**. This isn't "preceding diabetes" (you already have a diagnosis), but indicates that the **metabolic component needs attention** alongside your main therapy.

{% if on_statins %}You're on statins — this reduces cardiovascular events but has limited effect on triglycerides and HDL. If TG remains high, discuss high-dose omega-3 or fibrates with your cardiologist.{% endif %}

In diabetics, elevated TG and low HDL are **part of the clinical picture**, but require their own focus to reduce cardiovascular risk.
{% else %}
The combination in your results — elevated triglycerides, low HDL{% if alt %}, mildly elevated ALT ({{ alt }} U/L){% endif %} — is typical of **insulin resistance and non-alcoholic fatty liver disease (NAFLD)**. This often precedes diabetes and metabolic syndrome.

This isn't a "disease with symptoms" but rather a **metabolic disturbance** that develops gradually with excess weight, sedentary lifestyle, and high sugar/refined carb intake.
{% endif %}
---
actions:
{% if has_diabetes %}
- Discuss results with endocrinologist or cardiologist — may need **intensified lipid therapy**
- Diabetic targets: **LDL <70 mg/dL** (high risk) or **<55 mg/dL** (very high risk if existing complications)
- Regular activity (150 min/wk aerobic + 2 strength sessions) — affects TG/HDL more than diet
- If overweight — even 5-7% weight loss improves all metabolic markers
- Consider liver ultrasound — NAFLD is a common comorbidity in diabetics
- Repeat lipid panel and liver enzymes in 3-6 months
{% if not on_statins %}- Discuss statin initiation with your physician — almost always indicated in diabetics{% endif %}
{% else %}
- See a GP or endocrinologist for full lipid and metabolic profile
- Additional: HbA1c, TSH, ferritin, liver ultrasound
- Review diet — Mediterranean-style works best
- Regular activity (150 min/wk aerobic + 2 strength sessions)
- If overweight — target 5-10% weight loss over 6 months
- Limit alcohol
- Repeat tests in 6 months
{% endif %}
---
red_flags:
- Pain in upper-right abdomen
- Persistent fatigue, abdominal heaviness
- Yellowing of skin or eyes
{% if has_diabetes %}- Chest pain on exertion — CVD often presents atypically in diabetics{% endif %}
{% if on_statins %}- Severe muscle pain or dark urine — possible statin rhabdomyolysis{% endif %}
