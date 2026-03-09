# {% if has_diabetes %}Glycemic control — near target ceiling{% else %}Prediabetes range{% endif %}
icon: 🩸
severity: low
---
{% if has_diabetes %}
Diabetes is already in your profile. Current values — {% if a1c %}HbA1c {{ a1c }}%{% endif %}{% if a1c and glucose %} and {% endif %}{% if glucose %}fasting glucose {{ glucose }} mg/dL{% endif %} — **do not indicate a new problem** and do not mean "prediabetes" (a term that applies only to people without an established diagnosis).

For diabetics, ADA recommends a target **HbA1c < 7%** for most adults{% if a1c and a1c < 7.0 %} — your value of {{ a1c }}% falls within this range, **control is adequate**.{% elif a1c and a1c < 7.5 %} — your value of {{ a1c }}% is **approaching the upper limit** but not yet beyond it.{% else %} — your value is above target and needs therapy intensification.{% endif %} In select cases (young, no complications) a target <6.5% may be considered, but this is individualised with the endocrinologist.

{% if takes_metformin or on_oral_diabetics %}**Do not stop current therapy** — the numbers show it is working. If levels start drifting up, discuss dose adjustment with the endocrinologist.{% endif %}
{% else %}
{% if a1c %}Your HbA1c — {{ a1c }}% — is in the prediabetes range (5.7-6.4%).{% endif %}{% if glucose %} Fasting glucose {{ glucose }} mg/dL is also on the upper end.{% endif %}

**This is not diabetes**, but it signals that your body is starting to handle sugar poorly. Without lifestyle changes, about 30-50% of people with prediabetes develop full diabetes within 5 years. The good news: **this is reversible** with the right actions.
{% endif %}
---
actions:
{% if has_diabetes %}
- **Routine HbA1c monitoring** — standard every 3 months
- Home glucose self-monitoring per your physician's schedule
- Continue regular endocrinologist visits (every 3-6 months)
- Do not stop current medications on your own
- Control other risk factors: BP, lipids (LDL targets are stricter for diabetics)
- Healthy lifestyle — exercise, diet, weight — remains critically important **on top of therapy**
{% else %}
- Reduce fast carbs (sweets, white flour, sweetened drinks, fruit juices)
- Increase activity to 150 min/week of moderate exercise (brisk walking works)
- If overweight, even **5-7% weight loss** often restores metabolic health
- Repeat HbA1c in 6 months
- See your GP to evaluate other risk factors (BP, lipids)
{% endif %}
---
red_flags:
{% if has_diabetes %}
- A sharp rise in HbA1c at the next measurement
- Frequent hypoglycemia (tremor, cold sweat, hunger) — needs dose adjustment
- Sudden vision changes, non-healing foot wounds
{% else %}
- If HbA1c continues to rise on repeat testing
- Onset of diabetes symptoms: severe thirst, frequent urination, fatigue
{% endif %}
