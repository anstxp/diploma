# {% if has_any_chronic %}Metabolic syndrome — intensified monitoring and therapy review{% else %}Multi-system cardiometabolic risk{% endif %}
icon: 🚨
severity: high
---
{% if has_any_chronic %}
The analysis shows **elevated risk across multiple domains** simultaneously — cardiovascular, metabolic, lipid. You have a chronic condition in your profile{% if on_any_therapy %}, and you're on therapy{% endif %} — this constellation means that **current strategy needs review**.

Key findings:
{% if p_htn %}- Hypertension: {{ p_htn }}% (×{{ ratio_htn }} vs population){% endif %}
{% if p_diabetes %}- Diabetes: {{ p_diabetes }}% (×{{ ratio_diabetes }}){% endif %}
{% if p_high_chol %}- High cholesterol: {{ p_high_chol }}% (×{{ ratio_high_chol }}){% endif %}
{% if p_chd %}- Coronary heart disease: {{ p_chd }}% (×{{ ratio_chd }}){% endif %}

{% if on_statins or on_acei_arb or on_antihypertensives or takes_metformin or on_oral_diabetics %}**Do not stop current therapy on your own** — discuss intensification or adjustment with your physician. In this constellation, inadequate therapy = compounded risk.{% endif %}
{% else %}
The analysis flagged **elevated risk across multiple systems** — cardiovascular, metabolic, lipid. This constellation matters more than any single abnormality: these risks reinforce each other, and your risk of complications is higher than the sum of its parts.

Key findings:
{% if p_htn %}- Hypertension: {{ p_htn }}% (×{{ ratio_htn }} vs population){% endif %}
{% if p_diabetes %}- Diabetes: {{ p_diabetes }}% (×{{ ratio_diabetes }}){% endif %}
{% if p_high_chol %}- High cholesterol: {{ p_high_chol }}% (×{{ ratio_high_chol }}){% endif %}
{% if p_chd %}- Coronary heart disease: {{ p_chd }}% (×{{ ratio_chd }}){% endif %}

Good news — most of these risks are **modifiable** with comprehensive lifestyle and medical management.
{% endif %}
---
actions:
{% if has_any_chronic %}
- **See your GP or cardiologist — unscheduled visit** for strategy review
- Get repeat fasting lipids, HbA1c, creatinine with eGFR, urine ACR
- Home BP morning and evening for 7 days
- **Do not stop current medications on your own**
{% if has_diabetes %}- Stricter targets: HbA1c <7%, LDL <70 mg/dL (<55 at very high risk), BP <130/80{% endif %}
- Regular aerobic activity 150 min/week
- Mediterranean or DASH diet
{% else %}
- **See a GP or cardiologist within 1-2 weeks**
- Get repeat fasting lipids, HbA1c, creatinine with eGFR, urine microalbumin
- Measure home BP morning and evening for 7 days
{% if bmi and bmi >= 30 %}- 5-10% weight loss meaningfully reduces all these risks{% endif %}
- Regular aerobic activity, 150 min/week (brisk walking, swimming)
- Mediterranean or DASH diet (vegetables, fish, olive oil, less red meat)
- **Quit smoking** and **limit alcohol**
- If statin or BP medication is prescribed, take consistently
{% endif %}
---
red_flags:
- Chest pain radiating to arm, neck, or jaw — **call emergency**
- Severe headache with nausea or visual disturbance
- Sudden weakness on one side, slurred speech — possible **stroke**
- Shortness of breath with mild exertion, leg swelling — possible heart failure
- Systolic BP >180 or diastolic >120 — hypertensive crisis
