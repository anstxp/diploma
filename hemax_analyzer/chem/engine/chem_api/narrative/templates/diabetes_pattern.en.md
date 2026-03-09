{% if has_diabetes %}# Diabetes control{% endif %}{% if not_known_diabetic %}# Diabetes pattern{% endif %}
icon: 🩸
severity: medium
---
{% if has_diabetes %}Your profile lists diabetes. Current numbers: {% if a1c %}HbA1c — **{{ a1c }}%**{% endif %}{% if glucose %} fasting glucose **{{ glucose }} mg/dL**{% endif %}.

{% if a1c_above_target %}HbA1c is above the **7.0% target** — glycemic control needs work. This **isn't a failure** — diabetes is a marathon, and adjusting the regimen periodically is normal.{% endif %}{% if a1c_at_target %}HbA1c is on target — glycemia is well-controlled. Keep it up!{% endif %}

Standard target for most adults with diabetes: HbA1c <7%, fasting glucose 80–130 mg/dL (4.4–7.2 mmol/L). The exact target depends on age, diabetes duration and comorbidities — discuss with your endocrinologist.{% endif %}{% if not_known_diabetic %}{% if a1c %}Your HbA1c — {{ a1c }}% — is in the diabetes range (≥6.5%).{% endif %}{% if glucose %} Fasting glucose {{ glucose }} mg/dL is also elevated.{% endif %} This very likely indicates **diabetes mellitus**, though an official diagnosis requires repeat testing (or OGTT).

HbA1c reflects your **average blood sugar over the past 2-3 months**, making it more stable than a single glucose measurement. With modern care, diabetes is a manageable condition — people live full lives without complications.{% endif %}
---
actions:
{% if has_diabetes %}
- **Bring the results to your endocrinologist** at the next routine visit (sooner if HbA1c >8%)
- Self-monitor glucose (fasting + post-meal) per your doctor's plan
- Revisit diet and exercise — often helps more than medication changes
- Yearly: eye exam, foot check, urine microalbumin, creatinine
- If overweight, even a 5% weight loss meaningfully improves glycemia
{% endif %}
{% if not_known_diabetic %}
- **See an endocrinologist or GP within 1-2 weeks**
- Repeat HbA1c in 4-6 weeks to confirm
- Check kidney function (creatinine, urine microalbumin) and eyes (ophthalmology)
- Review diet: reduce fast carbs, sugar, sweetened drinks
- Start regular moderate exercise (30 min/day)
- If overweight, discuss a weight-loss plan with your doctor
{% endif %}
---
red_flags:
- Severe thirst + frequent urination + weight loss — see a doctor urgently
- Fruity breath, nausea, abdominal pain — possible ketoacidosis — **go to ER**
- Blurred or worsening vision
- Non-healing wounds on feet
{% if has_diabetes %}
- Frequent hypoglycemia (shakiness, cold sweats, hunger) — needs dose adjustment
{% endif %}
